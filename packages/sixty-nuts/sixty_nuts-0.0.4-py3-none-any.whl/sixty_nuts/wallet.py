from __future__ import annotations

from enum import IntEnum
from typing import Literal, TypedDict
import base64
import hashlib
import json
import secrets
import time
from dataclasses import dataclass
import asyncio

import httpx
from coincurve import PrivateKey, PublicKey

from .mint import Mint, Proof, BlindedMessage
from .relay import NostrRelay, NostrEvent, RelayError
from .crypto import (
    blind_message,
    unblind_signature,
    NIP44Encrypt,
    hash_to_curve,
)

try:
    from bech32 import bech32_decode, convertbits  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – allow runtime miss
    bech32_decode = None  # type: ignore
    convertbits = None  # type: ignore

try:
    import cbor2
except ModuleNotFoundError:  # pragma: no cover – allow runtime miss
    cbor2 = None  # type: ignore


# ──────────────────────────────────────────────────────────────────────────────
# Protocol-level definitions
# ──────────────────────────────────────────────────────────────────────────────


class EventKind(IntEnum):
    """Nostr event kinds relevant to NIP-60."""

    RELAY_RECOMMENDATIONS = 10019
    Wallet = 17375  # wallet metadata
    Token = 7375  # unspent proofs
    History = 7376  # optional transaction log
    QuoteTracker = 7374  # mint quote tracker (optional)
    Delete = 5  # NIP-09 delete event


class ProofDict(TypedDict):
    id: str
    amount: int
    secret: str
    C: str


@dataclass
class WalletState:
    """Current wallet state."""

    balance: int
    proofs: list[ProofDict]
    mint_keysets: dict[str, list[dict[str, str]]]  # mint_url -> keysets
    proof_to_event_id: dict[str, str] | None = (
        None  # proof_id -> event_id mapping (TODO)
    )


Direction = Literal["in", "out"]


class WalletError(Exception):
    """Base class for wallet errors."""


# ──────────────────────────────────────────────────────────────────────────────
# Wallet implementation skeleton
# ──────────────────────────────────────────────────────────────────────────────


class Wallet:
    """Lightweight stateless Cashu wallet implementing NIP-60."""

    def __init__(
        self,
        nsec: str,  # nostr private key
        *,
        mint_urls: list[str] | None = None,  # cashu mint urls (can have multiple)
        currency: Literal["sat", "msat", "usd"] = "sat",
        wallet_privkey: str | None = None,  # separate privkey for P2PK ecash (NIP-61)
        relays: list[str] | None = None,  # nostr relays to use
    ) -> None:
        self.nsec = nsec
        self._privkey = self._decode_nsec(nsec)
        self.mint_urls: list[str] = mint_urls or ["https://mint.minibits.cash/Bitcoin"]
        self.currency = currency
        # Generate wallet privkey if not provided
        if wallet_privkey is None:
            wallet_privkey = self._generate_privkey()
        self.wallet_privkey = wallet_privkey
        self._wallet_privkey_obj = PrivateKey(bytes.fromhex(wallet_privkey))

        self.relays: list[str] = relays or [
            "wss://relay.damus.io",
            "wss://relay.nostr.band",
            "wss://nos.lol",
            "wss://nostr.wine",
            "wss://relay.snort.social",
            "wss://nostr.mom",
        ]

        # Mint and relay instances
        self.mints: dict[str, Mint] = {}
        self.relay_instances: list[NostrRelay] = []

        # Track minted quotes to prevent double-minting
        self._minted_quotes: set[str] = set()

        # Shared HTTP client reused by all Mint objects
        self.mint_client = httpx.AsyncClient()

        # Cache for proof validation results to prevent re-checking spent proofs
        self._proof_state_cache: dict[
            str, dict[str, str]
        ] = {}  # proof_id -> {state, timestamp}
        self._cache_expiry = 300  # 5 minutes

        # Track known spent proofs to avoid re-validation
        self._known_spent_proofs: set[str] = set()

        # Rate limiting for relay operations
        self._last_relay_operation = 0.0
        self._min_relay_interval = 1.0  # Minimum 1 second between operations

    # ───────────────────────── Crypto Helpers ─────────────────────────────────

    def _create_blinded_message(
        self, amount: int, keyset_id: str
    ) -> tuple[str, str, BlindedMessage]:
        """Create a properly blinded message for the mint.

        Returns:
            Tuple of (secret, blinding_factor_hex, BlindedMessage)
        """
        # Generate random 32-byte secret
        secret_bytes = secrets.token_bytes(32)

        # Convert to hex string (this is what Cashu protocol expects)
        secret_hex = secret_bytes.hex()

        # For blinding, use UTF-8 bytes of the hex string (Cashu standard)
        secret_utf8_bytes = secret_hex.encode("utf-8")

        # Blind the message using the UTF-8 encoded hex string
        B_, r = blind_message(secret_utf8_bytes)

        # Convert to hex for storage
        B_hex = B_.format(compressed=True).hex()
        r_hex = r.hex()

        # For NIP-60 storage, convert to base64
        secret_base64 = base64.b64encode(secret_bytes).decode("ascii")

        return (
            secret_base64,  # Store as base64 string in proof (NIP-60 requirement)
            r_hex,
            BlindedMessage(
                amount=amount,
                id=keyset_id,
                B_=B_hex,
            ),
        )

    def _get_mint_pubkey_for_amount(
        self, keys_data: dict[str, str], amount: int
    ) -> PublicKey | None:
        """Get the mint's public key for a specific amount.

        Args:
            keys_data: Dictionary mapping amounts to public keys
            amount: The denomination amount

        Returns:
            PublicKey or None if not found
        """
        # Keys are indexed by string amount
        pubkey_hex = keys_data.get(str(amount))
        if pubkey_hex:
            return PublicKey(bytes.fromhex(pubkey_hex))
        return None

    def _decode_nsec(self, nsec: str) -> PrivateKey:
        """Decode `nsec` (bech32 as per Nostr) or raw hex private key."""
        if nsec.startswith("nsec1"):
            if bech32_decode is None or convertbits is None:
                raise NotImplementedError(
                    "bech32 library missing – install `bech32` to use bech32-encoded nsec keys"
                )

            hrp, data = bech32_decode(nsec)
            if hrp != "nsec" or data is None:
                raise ValueError("Malformed nsec bech32 string")

            decoded = bytes(convertbits(data, 5, 8, False))  # type: ignore
            if len(decoded) != 32:
                raise ValueError("Invalid nsec length after decoding")
            return PrivateKey(decoded)

        # Fallback – treat as raw hex key
        return PrivateKey(bytes.fromhex(nsec))

    def _generate_privkey(self) -> str:
        """Generate a new secp256k1 private key for wallet P2PK operations."""
        return PrivateKey().to_hex()

    def _get_pubkey(self, privkey: PrivateKey | None = None) -> str:
        """Get hex public key from private key (defaults to main nsec)."""
        if privkey is None:
            privkey = self._privkey
        # Nostr uses x-only public keys (32 bytes, without the prefix byte)
        compressed_pubkey = privkey.public_key.format(compressed=True)
        x_only_pubkey = compressed_pubkey[1:]  # Remove the prefix byte
        return x_only_pubkey.hex()

    def _get_pubkey_compressed(self, privkey: PrivateKey | None = None) -> str:
        """Get full compressed hex public key for encryption (33 bytes)."""
        if privkey is None:
            privkey = self._privkey
        return privkey.public_key.format(compressed=True).hex()

    def _sign_event(self, event: dict) -> dict:
        """Sign a Nostr event with the user's private key."""
        # Ensure event has required fields
        event["pubkey"] = self._get_pubkey()
        event["created_at"] = event.get("created_at", int(time.time()))
        event["id"] = self._compute_event_id(event)

        # Sign the event
        sig = self._privkey.sign_schnorr(bytes.fromhex(event["id"]))
        event["sig"] = sig.hex()

        return event

    def _compute_event_id(self, event: dict) -> str:
        """Compute Nostr event ID (hash of canonical JSON)."""
        # Canonical format: [0, pubkey, created_at, kind, tags, content]
        canonical = json.dumps(
            [
                0,
                event["pubkey"],
                event["created_at"],
                event["kind"],
                event["tags"],
                event["content"],
            ],
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    # ───────────────────────── NIP-44 Encryption ─────────────────────────────────

    def _nip44_encrypt(
        self, plaintext: str, recipient_pubkey: str | None = None
    ) -> str:
        """Encrypt content using NIP-44 v2."""
        if recipient_pubkey is None:
            recipient_pubkey = self._get_pubkey_compressed()

        return NIP44Encrypt.encrypt(plaintext, self._privkey, recipient_pubkey)

    def _nip44_decrypt(self, ciphertext: str, sender_pubkey: str | None = None) -> str:
        """Decrypt content using NIP-44 v2."""
        if sender_pubkey is None:
            sender_pubkey = self._get_pubkey_compressed()

        return NIP44Encrypt.decrypt(ciphertext, self._privkey, sender_pubkey)

    def _create_event(
        self,
        kind: int,
        content: str = "",
        tags: list[list[str]] | None = None,
    ) -> dict:
        """Create unsigned Nostr event structure."""
        return {
            "kind": kind,
            "content": content,
            "tags": tags or [],
            "created_at": int(time.time()),
        }

    # ───────────────────────── Helper Methods ─────────────────────────────────

    def _get_mint(self, mint_url: str) -> Mint:
        """Get or create mint instance for URL."""
        if mint_url not in self.mints:
            self.mints[mint_url] = Mint(mint_url, client=self.mint_client)
        return self.mints[mint_url]

    async def _get_relay_connections(self) -> list[NostrRelay]:
        """Get relay connections, discovering if needed."""
        if not self.relay_instances:
            # Try to discover relays
            discovered_relays = await self._discover_relays()
            relay_urls = discovered_relays or self.relays

            # Try to connect to relays
            for url in relay_urls[:5]:  # Try up to 5 relays
                try:
                    relay = NostrRelay(url)
                    await relay.connect()
                    self.relay_instances.append(relay)

                    # Stop after successfully connecting to 3 relays
                    if len(self.relay_instances) >= 3:
                        break
                except Exception:
                    continue

            if not self.relay_instances:
                raise RelayError("Could not connect to any relay")

        return self.relay_instances

    async def _discover_relays(self) -> list[str]:
        """Discover relays from kind:10019 events."""
        # Use a well-known relay to bootstrap
        bootstrap_relay = NostrRelay("wss://relay.damus.io")
        try:
            await bootstrap_relay.connect()
            relays = await bootstrap_relay.fetch_relay_recommendations(
                self._get_pubkey()
            )
            return relays
        except Exception:
            return []
        finally:
            await bootstrap_relay.disconnect()

    async def _rate_limit_relay_operations(self) -> None:
        """Apply rate limiting to relay operations."""
        now = time.time()
        time_since_last = now - self._last_relay_operation
        if time_since_last < self._min_relay_interval:
            await asyncio.sleep(self._min_relay_interval - time_since_last)
        self._last_relay_operation = time.time()

    def _estimate_event_size(self, event: dict) -> int:
        """Estimate the size of an event in bytes."""
        return len(json.dumps(event, separators=(",", ":")))

    async def _publish_to_relays(self, event: dict) -> str:
        """Publish event to all relays and return event ID."""
        # Apply rate limiting
        await self._rate_limit_relay_operations()

        relays = await self._get_relay_connections()
        event_dict = NostrEvent(**event)  # type: ignore

        # Try to publish to at least one relay
        published = False
        errors = []

        for relay in relays:
            try:
                if await relay.publish_event(event_dict):
                    published = True
                else:
                    errors.append(f"{relay.url}: Event rejected")
            except Exception as e:
                errors.append(f"{relay.url}: {str(e)}")
                continue

        if not published:
            # Only log if we can't publish anywhere to avoid log spam
            error_msg = f"Failed to publish event to any relay. Last error: {errors[-1] if errors else 'Unknown'}"
            print(f"Warning: {error_msg}")
            # Don't raise exception - allow operations to continue
            return event["id"]

        return event["id"]

    def _serialize_proofs_for_token(
        self, proofs: list[ProofDict], mint_url: str
    ) -> str:
        """Serialize proofs into a Cashu token format."""
        # Convert ProofDict (with base64 secrets) to format expected by Cashu tokens (hex secrets)
        token_proofs = []
        for proof in proofs:
            # Convert base64 secret to hex for Cashu token
            try:
                secret_bytes = base64.b64decode(proof["secret"])
                secret_hex = secret_bytes.hex()
            except Exception:
                # Fallback: assume it's already hex
                secret_hex = proof["secret"]

            token_proofs.append(
                {
                    "id": proof["id"],
                    "amount": proof["amount"],
                    "secret": secret_hex,  # Cashu tokens expect hex
                    "C": proof["C"],
                }
            )

        # Cashu token format: cashuA<base64url(json)>
        token_data = {
            "token": [{"mint": mint_url, "proofs": token_proofs}],
            "unit": self.currency,
            "memo": "NIP-60 wallet transfer",
        }
        json_str = json.dumps(token_data, separators=(",", ":"))
        encoded = base64.urlsafe_b64encode(json_str.encode()).decode().rstrip("=")
        return f"cashuA{encoded}"

    def _parse_cashu_token(self, token: str) -> tuple[str, str, list[ProofDict]]:
        """Parse Cashu token and return (mint_url, proofs)."""
        if not token.startswith("cashu"):
            raise ValueError("Invalid token format")

        # Check token version
        if token.startswith("cashuA"):
            # Version 3 - JSON format
            encoded = token[6:]  # Remove "cashuA"
            # Add correct padding – (-len) % 4 equals 0,1,2,3
            encoded += "=" * ((-len(encoded)) % 4)

            decoded = base64.urlsafe_b64decode(encoded).decode()
            token_data = json.loads(decoded)

            # Extract mint and proofs from JSON format
            mint_info = token_data["token"][0]
            unit = token_data["unit"]
            token_proofs = mint_info["proofs"]

            # Convert hex secrets to base64 for NIP-60 storage
            nip60_proofs: list[ProofDict] = []
            for proof in token_proofs:
                # Convert hex secret to base64
                try:
                    secret_bytes = bytes.fromhex(proof["secret"])
                    secret_base64 = base64.b64encode(secret_bytes).decode("ascii")
                except Exception:
                    # Fallback: assume it's already base64
                    secret_base64 = proof["secret"]

                nip60_proofs.append(
                    ProofDict(
                        id=proof["id"],
                        amount=proof["amount"],
                        secret=secret_base64,  # Store as base64 for NIP-60
                        C=proof["C"],
                    )
                )

            return mint_info["mint"], unit, nip60_proofs

        elif token.startswith("cashuB"):
            # Version 4 - CBOR format
            if cbor2 is None:
                raise ImportError("cbor2 library required for cashuB tokens")

            encoded = token[6:]  # Remove "cashuB"
            # Add padding for base64
            encoded += "=" * ((-len(encoded)) % 4)

            decoded_bytes = base64.urlsafe_b64decode(encoded)
            token_data = cbor2.loads(decoded_bytes)

            # Extract from CBOR format - different structure
            # 'm' = mint URL, 'u' = unit, 't' = tokens array
            mint_url = token_data["m"]
            unit = token_data["u"]
            proofs = []

            # Each token in 't' has 'i' (keyset id) and 'p' (proofs)
            for token_entry in token_data["t"]:
                keyset_id = token_entry["i"].hex()  # Convert bytes to hex
                for proof in token_entry["p"]:
                    # CBOR format already has hex secret, convert to base64
                    secret_hex = proof["s"]
                    try:
                        secret_bytes = bytes.fromhex(secret_hex)
                        secret_base64 = base64.b64encode(secret_bytes).decode("ascii")
                    except Exception:
                        # Fallback
                        secret_base64 = secret_hex

                    # Convert CBOR proof format to our ProofDict format
                    proofs.append(
                        ProofDict(
                            id=keyset_id,
                            amount=proof["a"],
                            secret=secret_base64,  # Store as base64 for NIP-60
                            C=proof["c"].hex(),  # Convert bytes to hex
                        )
                    )

            return mint_url, unit, proofs
        else:
            raise ValueError(f"Unknown token version: {token[:7]}")

    # ───────────────────────── Wallet State Management ─────────────────────────

    async def create_wallet_event(self) -> str:
        """Create or update the replaceable wallet event (kind 17375).

        Returns the published event id.
        """
        # Create content array with wallet metadata
        content_data = [
            ["privkey", self.wallet_privkey],
        ]
        for mint_url in self.mint_urls:
            content_data.append(["mint", mint_url])

        # Encrypt content
        content_json = json.dumps(content_data)
        encrypted_content = self._nip44_encrypt(content_json)

        # NIP-60 requires at least one mint tag in the tags array (unencrypted)
        # This is critical for wallet discovery!
        tags = [["mint", url] for url in self.mint_urls]

        # Create replaceable wallet event
        event = self._create_event(
            kind=EventKind.Wallet,
            content=encrypted_content,
            tags=tags,
        )

        # Sign and publish
        signed_event = self._sign_event(event)
        return await self._publish_to_relays(signed_event)

    def _compute_proof_y_values(self, proofs: list[ProofDict]) -> list[str]:
        """Compute Y values for proofs to use in check_state API.

        Args:
            proofs: List of proof dictionaries

        Returns:
            List of Y values (hex encoded compressed public keys)
        """
        y_values = []
        for proof in proofs:
            # NIP-60 stores secrets as base64
            secret_base64 = proof["secret"]
            try:
                # Decode base64 to get raw secret bytes
                secret_bytes = base64.b64decode(secret_base64)
                # Convert to hex string
                secret_hex = secret_bytes.hex()
            except Exception:
                # Fallback for hex-encoded secrets (backwards compatibility)
                secret_hex = proof["secret"]

            # Hash to curve point using UTF-8 bytes of hex string (Cashu standard)
            secret_utf8_bytes = secret_hex.encode("utf-8")
            Y = hash_to_curve(secret_utf8_bytes)
            # Convert to compressed hex format
            y_hex = Y.format(compressed=True).hex()
            y_values.append(y_hex)
        return y_values

    def _is_proof_state_cached(self, proof_id: str) -> tuple[bool, str | None]:
        """Check if proof state is cached and still valid."""
        if proof_id in self._proof_state_cache:
            cache_entry = self._proof_state_cache[proof_id]
            timestamp = float(cache_entry.get("timestamp", 0))
            if time.time() - timestamp < self._cache_expiry:
                return True, cache_entry.get("state")
        return False, None

    def _cache_proof_state(self, proof_id: str, state: str) -> None:
        """Cache proof state with timestamp."""
        self._proof_state_cache[proof_id] = {
            "state": state,
            "timestamp": str(time.time()),
        }

        # Track spent proofs separately for faster lookup
        if state == "SPENT":
            self._known_spent_proofs.add(proof_id)

    def clear_spent_proof_cache(self) -> None:
        """Clear the spent proof cache to prevent memory growth."""
        self._proof_state_cache.clear()
        self._known_spent_proofs.clear()

    async def _validate_proofs_with_cache(
        self, proofs: list[ProofDict]
    ) -> list[ProofDict]:
        """Validate proofs using cache to avoid re-checking spent proofs."""
        valid_proofs = []
        proofs_to_check: list[ProofDict] = []

        # First pass: check cache and filter out known spent proofs
        for proof in proofs:
            proof_id = f"{proof['secret']}:{proof['C']}"

            # Skip known spent proofs immediately
            if proof_id in self._known_spent_proofs:
                continue

            is_cached, cached_state = self._is_proof_state_cached(proof_id)
            if is_cached:
                if cached_state == "UNSPENT":
                    valid_proofs.append(proof)
                # SPENT proofs are filtered out (don't add to valid_proofs)
            else:
                proofs_to_check.append(proof)

        # Second pass: validate uncached proofs
        if proofs_to_check:
            # Group by mint for batch validation
            proofs_by_mint: dict[str, list[ProofDict]] = {}
            for proof in proofs_to_check:
                # Use first mint URL for all proofs (could be improved)
                mint_url = self.mint_urls[0] if self.mint_urls else None
                if mint_url:
                    if mint_url not in proofs_by_mint:
                        proofs_by_mint[mint_url] = []
                    proofs_by_mint[mint_url].append(proof)

            # Validate with each mint
            for mint_url, mint_proofs in proofs_by_mint.items():
                try:
                    mint = self._get_mint(mint_url)
                    y_values = self._compute_proof_y_values(mint_proofs)
                    state_response = await mint.check_state(Ys=y_values)

                    for i, proof in enumerate(mint_proofs):
                        proof_id = f"{proof['secret']}:{proof['C']}"
                        if i < len(state_response["states"]):
                            state_info = state_response["states"][i]
                            state = state_info.get("state", "UNKNOWN")

                            # Cache the result
                            self._cache_proof_state(proof_id, state)

                            # Only include unspent proofs
                            if state == "UNSPENT":
                                valid_proofs.append(proof)

                        else:
                            # No state info - assume valid but don't cache
                            valid_proofs.append(proof)

                except Exception:
                    # If validation fails, include proofs but don't cache
                    valid_proofs.extend(mint_proofs)

        return valid_proofs

    async def fetch_wallet_state(self, *, check_proofs: bool = True) -> WalletState:
        """Fetch wallet, token events and compute balance.

        Args:
            check_proofs: If True, validate all proofs with mint before returning state
        """
        relays = await self._get_relay_connections()
        pubkey = self._get_pubkey()

        # Fetch all wallet-related events
        all_events: list[NostrEvent] = []
        event_ids_seen: set[str] = set()

        for relay in relays:
            try:
                events = await relay.fetch_wallet_events(pubkey)
                # Deduplicate events
                for event in events:
                    if event["id"] not in event_ids_seen:
                        all_events.append(event)
                        event_ids_seen.add(event["id"])
            except Exception:
                continue

        # Find wallet event
        wallet_event = None
        for event in all_events:
            if event["kind"] == EventKind.Wallet:
                wallet_event = event
                break

        # Parse wallet metadata
        if wallet_event:
            decrypted = self._nip44_decrypt(wallet_event["content"])
            wallet_data = json.loads(decrypted)

            # Update mint URLs from wallet event
            self.mint_urls = []
            for item in wallet_data:
                if item[0] == "mint":
                    self.mint_urls.append(item[1])
                elif item[0] == "privkey":
                    self.wallet_privkey = item[1]

        # Collect token events
        token_events = [e for e in all_events if e["kind"] == EventKind.Token]

        # Track deleted token events
        deleted_ids = set()
        for event in all_events:
            if event["kind"] == EventKind.Delete:
                for tag in event["tags"]:
                    if tag[0] == "e":
                        deleted_ids.add(tag[1])

        # Aggregate unspent proofs taking into account NIP-60 roll-overs and avoiding duplicates
        all_proofs: list[ProofDict] = []
        proof_to_event_id: dict[str, str] = {}

        # Index events newest → oldest so that when we encounter a replacement first we can ignore the ones it deletes later
        token_events_sorted = sorted(
            token_events, key=lambda e: e["created_at"], reverse=True
        )

        invalid_token_ids: set[str] = set(deleted_ids)
        proof_seen: set[str] = set()

        for event in token_events_sorted:
            if event["id"] in invalid_token_ids:
                continue

            decrypted = self._nip44_decrypt(event["content"])
            token_data = json.loads(decrypted)

            # Mark tokens referenced in the "del" field as superseded
            for old_id in token_data.get("del", []):
                invalid_token_ids.add(old_id)

            if event["id"] in invalid_token_ids:
                continue

            proofs = token_data.get("proofs", [])

            for proof in proofs:
                proof_id = f"{proof['secret']}:{proof['C']}"
                if proof_id in proof_seen:
                    continue
                proof_seen.add(proof_id)
                all_proofs.append(proof)
                proof_to_event_id[proof_id] = event["id"]

        # Validate proofs using cache system if requested
        if check_proofs and all_proofs:
            all_proofs = await self._validate_proofs_with_cache(all_proofs)

        # Calculate balance
        balance = sum(p["amount"] for p in all_proofs)

        # Fetch mint keysets
        mint_keysets = {}
        for mint_url in self.mint_urls:
            mint = self._get_mint(mint_url)
            try:
                keys_resp = await mint.get_keys()
                mint_keysets[mint_url] = keys_resp.get("keysets", [])
            except Exception:
                mint_keysets[mint_url] = []

        return WalletState(
            balance=balance,
            proofs=all_proofs,
            mint_keysets=mint_keysets,
            proof_to_event_id=proof_to_event_id,
        )

    async def get_balance(self, *, check_proofs: bool = True) -> int:
        """Get current wallet balance.

        Args:
            check_proofs: If True, validate all proofs with mint before returning balance

        Returns:
            Current balance in the wallet's currency unit

        Example:
            balance = await wallet.get_balance()
            print(f"Balance: {balance} sats")
        """
        state = await self.fetch_wallet_state(check_proofs=check_proofs)
        return state.balance

    # ───────────────────────────── Token Events ───────────────────────────────

    async def _split_large_token_events(
        self,
        proofs: list[ProofDict],
        mint_url: str,
        deleted_token_ids: list[str] | None = None,
    ) -> list[str]:
        """Split large token events into smaller chunks to avoid relay size limits."""
        if not proofs:
            return []

        # Maximum event size (leaving buffer for encryption overhead)
        max_size = 60000  # 60KB limit with buffer
        event_ids: list[str] = []
        current_batch: list[ProofDict] = []

        for proof in proofs:
            # Test adding this proof to current batch
            test_batch = current_batch + [proof]

            # Create test event content
            content_data = {
                "mint": mint_url,
                "proofs": test_batch,
            }

            # Add del field only to first event
            if deleted_token_ids and not event_ids:
                content_data["del"] = deleted_token_ids

            content_json = json.dumps(content_data)
            encrypted_content = self._nip44_encrypt(content_json)

            test_event = self._create_event(
                kind=EventKind.Token,
                content=encrypted_content,
                tags=[],
            )

            # Check if this would exceed size limit
            if self._estimate_event_size(test_event) > max_size and current_batch:
                # Current batch is full, create event and start new batch
                final_content_data = {
                    "mint": mint_url,
                    "proofs": current_batch,
                }

                # Add del field only to first event
                if deleted_token_ids and not event_ids:
                    final_content_data["del"] = deleted_token_ids

                final_content_json = json.dumps(final_content_data)
                final_encrypted_content = self._nip44_encrypt(final_content_json)

                final_event = self._create_event(
                    kind=EventKind.Token,
                    content=final_encrypted_content,
                    tags=[],
                )

                signed_event = self._sign_event(final_event)
                event_id = await self._publish_to_relays(signed_event)
                event_ids.append(event_id)
                current_batch = [proof]
            else:
                current_batch.append(proof)

        # Add final batch if not empty
        if current_batch:
            final_content_data = {
                "mint": mint_url,
                "proofs": current_batch,
            }

            # Add del field only to first event
            if deleted_token_ids and not event_ids:
                final_content_data["del"] = deleted_token_ids

            final_content_json = json.dumps(final_content_data)
            final_encrypted_content = self._nip44_encrypt(final_content_json)

            final_event = self._create_event(
                kind=EventKind.Token,
                content=final_encrypted_content,
                tags=[],
            )

            signed_event = self._sign_event(final_event)
            event_id = await self._publish_to_relays(signed_event)
            event_ids.append(event_id)

        return event_ids

    async def publish_token_event(
        self,
        proofs: list[ProofDict],
        *,
        deleted_token_ids: list[str] | None = None,
    ) -> str:
        """Publish encrypted token event (kind 7375) and return its id."""
        # First, delete old token events if specified
        if deleted_token_ids:
            for token_id in deleted_token_ids:
                await self.delete_token_event(token_id)

        # Assume all proofs are from the same mint (first mint URL)
        mint_url = self.mint_urls[0]

        # Check if we need to split the event due to size
        # Create a test event to estimate size
        content_data = {
            "mint": mint_url,
            "proofs": proofs,
        }

        if deleted_token_ids:
            content_data["del"] = deleted_token_ids

        content_json = json.dumps(content_data)
        encrypted_content = self._nip44_encrypt(content_json)

        test_event = self._create_event(
            kind=EventKind.Token,
            content=encrypted_content,
            tags=[],
        )

        # If event is too large, split it
        if self._estimate_event_size(test_event) > 60000:
            event_ids = await self._split_large_token_events(
                proofs, mint_url, deleted_token_ids
            )
            return event_ids[0] if event_ids else ""

        # Event is small enough, publish as single event
        signed_event = self._sign_event(test_event)
        return await self._publish_to_relays(signed_event)

    async def delete_token_event(self, event_id: str) -> None:
        """Delete a token event via NIP-09 (kind 5)."""
        # Create delete event
        event = self._create_event(
            kind=EventKind.Delete,
            content="",
            tags=[
                ["e", event_id],
                ["k", str(EventKind.Token.value)],
            ],
        )

        # Sign and publish
        signed_event = self._sign_event(event)
        await self._publish_to_relays(signed_event)

    # ──────────────────────────── History Events ──────────────────────────────

    async def publish_spending_history(
        self,
        *,
        direction: Literal["in", "out"],
        amount: int,
        created_token_ids: list[str] | None = None,
        destroyed_token_ids: list[str] | None = None,
        redeemed_event_id: str | None = None,
    ) -> str:
        """Publish kind 7376 spending history event and return its id."""
        # Build encrypted content
        content_data = [
            ["direction", direction],
            ["amount", str(amount)],
        ]

        # Add e-tags for created tokens (encrypted)
        if created_token_ids:
            for token_id in created_token_ids:
                content_data.append(["e", token_id, "", "created"])

        # Add e-tags for destroyed tokens (encrypted)
        if destroyed_token_ids:
            for token_id in destroyed_token_ids:
                content_data.append(["e", token_id, "", "destroyed"])

        # Encrypt content
        content_json = json.dumps(content_data)
        encrypted_content = self._nip44_encrypt(content_json)

        # Build tags (redeemed tags stay unencrypted)
        tags = []
        if redeemed_event_id:
            tags.append(["e", redeemed_event_id, "", "redeemed"])

        # Create history event
        event = self._create_event(
            kind=EventKind.History,
            content=encrypted_content,
            tags=tags,
        )

        # Sign and publish
        signed_event = self._sign_event(event)
        return await self._publish_to_relays(signed_event)

    # ─────────────────────────────── Receive ──────────────────────────────────

    async def redeem(self, token: str) -> tuple[int, str]:
        """Redeem a Cashu token into the wallet balance."""
        # Parse token
        mint_url, unit, proofs = self._parse_cashu_token(token)
        mint = self._get_mint(mint_url)

        # Convert to mint proof format
        mint_proofs: list[Proof] = []
        for p in proofs:
            mint_proofs.append(self._proofdict_to_mint_proof(p))

        # Create blinded messages for new proofs
        # In production, implement proper blinding
        outputs: list[BlindedMessage] = []
        secrets: list[str] = []
        blinding_factors: list[str] = []
        total_amount = sum(p["amount"] for p in proofs)

        # Simple denomination split using mint's active keyset id
        keys_resp_active = await mint.get_keys()
        keysets_active = keys_resp_active.get("keysets", [])
        keyset_id_active = (
            keysets_active[0]["id"] if keysets_active else proofs[0]["id"]
        )

        remaining = total_amount
        for denom in [64, 32, 16, 8, 4, 2, 1]:
            while remaining >= denom:
                secret, r_hex, blinded_msg = self._create_blinded_message(
                    denom, keyset_id_active
                )
                outputs.append(blinded_msg)
                secrets.append(secret)
                blinding_factors.append(r_hex)
                remaining -= denom

        # Swap proofs for new ones
        response = await mint.swap(inputs=mint_proofs, outputs=outputs)

        # Get mint public key for unblinding
        keys_resp = await mint.get_keys()
        # Find the keyset matching our proofs
        mint_keys = None
        for ks in keys_resp.get("keysets", []):
            if ks["id"] == keyset_id_active:
                keys_data: str | dict[str, str] = ks.get("keys", {})
                if isinstance(keys_data, dict) and keys_data:
                    mint_keys = keys_data
                    break

        if not mint_keys:
            raise WalletError("Could not find mint keys")

        # Convert signatures to proofs
        new_proofs: list[ProofDict] = []
        for i, sig in enumerate(response["signatures"]):
            # Get the public key for this amount
            amount = sig["amount"]
            mint_pubkey = self._get_mint_pubkey_for_amount(mint_keys, amount)
            if not mint_pubkey:
                raise WalletError(f"Could not find mint public key for amount {amount}")

            # Unblind the signature
            C_ = PublicKey(bytes.fromhex(sig["C_"]))
            r = bytes.fromhex(blinding_factors[i])
            C = unblind_signature(C_, r, mint_pubkey)

            new_proofs.append(
                ProofDict(
                    id=sig["id"],
                    amount=sig["amount"],
                    secret=secrets[i],
                    C=C.format(compressed=True).hex(),
                )
            )

        # Publish new token event
        token_event_id = await self.publish_token_event(new_proofs)

        # Publish spending history
        await self.publish_spending_history(
            direction="in",
            amount=total_amount,
            created_token_ids=[token_event_id],
        )

        return total_amount, unit

    async def create_quote(self, amount: int) -> tuple[str, str]:
        """Create a Lightning invoice (quote) at the mint and return the BOLT-11 string and quote ID.

        Returns:
            Tuple of (lightning_invoice, quote_id)
        """
        mint = self._get_mint(self.mint_urls[0])

        # Create mint quote
        quote_resp = await mint.create_mint_quote(
            unit=self.currency,
            amount=amount,
        )

        # Optionally publish quote tracker event
        # (skipping for simplicity)

        # TODO: Implement quote tracking as per NIP-60:
        # await self.publish_quote_tracker(
        #     quote_id=quote_resp["quote"],
        #     mint_url=self.mint_urls[0],
        #     expiration=int(time.time()) + 14 * 24 * 60 * 60  # 2 weeks
        # )

        return quote_resp["request"], quote_resp[
            "quote"
        ]  # Return both invoice and quote_id

    async def check_quote_status(
        self, quote_id: str, amount: int | None = None
    ) -> dict[str, object]:
        """Check whether a quote has been paid and redeem proofs if so."""
        mint = self._get_mint(self.mint_urls[0])

        # Check quote status
        quote_status = await mint.get_mint_quote(quote_id)

        if quote_status.get("paid") and quote_status.get("state") == "PAID":
            # Check if we've already minted for this quote
            if quote_id in self._minted_quotes:
                return dict(quote_status)

            # Mark this quote as being minted
            self._minted_quotes.add(quote_id)

            # Check if we've already minted for this quote
            # by seeing if we have a token event with this quote ID in tags
            # TODO: Properly track minted quotes to avoid double-minting
            # For now, we'll proceed with minting

            # Get amount from quote_status or use provided amount
            mint_amount = quote_status.get("amount", amount)
            if mint_amount is None:
                raise ValueError(
                    "Amount not available in quote status and not provided"
                )

            # Create blinded messages for the amount
            outputs: list[BlindedMessage] = []
            secrets: list[str] = []  # Keep track of secrets for creating proofs later
            blinding_factors: list[str] = []  # Track blinding factors

            # Get active keyset
            keys_resp = await mint.get_keys()
            keysets = keys_resp.get("keysets", [])
            keyset_id = keysets[0]["id"] if keysets else ""

            # Simple denomination split using mint's active keyset id
            keys_resp_active = await mint.get_keys()
            keysets_active = keys_resp_active.get("keysets", [])
            keyset_id_active = keysets_active[0]["id"] if keysets_active else keyset_id

            remaining = mint_amount
            for denom in [64, 32, 16, 8, 4, 2, 1]:
                while remaining >= denom:
                    secret, r_hex, blinded_msg = self._create_blinded_message(
                        denom, keyset_id_active
                    )
                    outputs.append(blinded_msg)
                    secrets.append(secret)
                    blinding_factors.append(r_hex)
                    remaining -= denom

            # Mint tokens
            mint_resp = await mint.mint(quote=quote_id, outputs=outputs)

            # Get mint public key for unblinding
            keys_resp = await mint.get_keys()
            mint_keys = None
            for ks in keys_resp.get("keysets", []):
                if ks["id"] == keyset_id_active:
                    keys_data: str | dict[str, str] = ks.get("keys", {})
                    if isinstance(keys_data, dict) and keys_data:
                        mint_keys = keys_data
                        break

            if not mint_keys:
                raise WalletError("Could not find mint keys")

            # Convert to proofs
            new_proofs: list[ProofDict] = []
            for i, sig in enumerate(mint_resp["signatures"]):
                # Get the public key for this amount
                amount = sig["amount"]
                mint_pubkey = self._get_mint_pubkey_for_amount(mint_keys, amount)
                if not mint_pubkey:
                    raise WalletError(
                        f"Could not find mint public key for amount {amount}"
                    )

                # Unblind the signature
                C_ = PublicKey(bytes.fromhex(sig["C_"]))
                r = bytes.fromhex(blinding_factors[i])
                C = unblind_signature(C_, r, mint_pubkey)

                new_proofs.append(
                    ProofDict(
                        id=sig["id"],
                        amount=sig["amount"],
                        secret=secrets[i],
                        C=C.format(compressed=True).hex(),
                    )
                )

            # Publish token event
            token_event_id = await self.publish_token_event(new_proofs)

            # Publish spending history
            await self.publish_spending_history(
                direction="in",
                amount=mint_amount,
                created_token_ids=[token_event_id],
            )

        return dict(quote_status)  # type: ignore

    async def mint_async(
        self, amount: int, *, timeout: int = 300
    ) -> tuple[str, asyncio.Task[bool]]:
        """Create a Lightning invoice and return a task that completes when paid.

        This returns immediately with the invoice and a background task that
        polls for payment.

        Args:
            amount: Amount in the wallet's currency unit
            timeout: Maximum seconds to wait for payment (default: 5 minutes)

        Returns:
            Tuple of (lightning_invoice, payment_task)
            The payment_task returns True when paid, False on timeout

        Example:
            invoice, task = await wallet.mint_async(100)
            print(f"Pay: {invoice}")
            # Do other things...
            paid = await task  # Wait for payment
        """
        invoice, quote_id = await self.create_quote(amount)

        async def poll_payment() -> bool:
            start_time = time.time()
            poll_interval = 1.0

            while (time.time() - start_time) < timeout:
                quote_status = await self.check_quote_status(quote_id, amount)
                if quote_status.get("paid"):
                    return True

                await asyncio.sleep(poll_interval)
                poll_interval = min(poll_interval * 1.2, 5.0)

            return False

        # Create background task
        task = asyncio.create_task(poll_payment())
        return invoice, task

    # ─────────────────────────────── Send ─────────────────────────────────────

    async def melt(self, invoice: str) -> None:
        """Pay a Lightning invoice using proofs (melt)."""
        mint = self._get_mint(self.mint_urls[0])

        # Get current wallet state with proof validation
        state = await self.fetch_wallet_state(check_proofs=True)

        # Create melt quote
        melt_quote = await mint.create_melt_quote(
            unit=self.currency,
            request=invoice,
        )

        quote_id = melt_quote["quote"]
        total_needed = melt_quote["amount"] + melt_quote["fee_reserve"]

        # Select proofs to spend
        # TODO: Implement better coin selection algorithm to minimize
        # the number of proofs used and optimize privacy
        selected_proofs: list[ProofDict] = []
        selected_amount = 0
        events_to_delete: set[str] = set()
        proof_to_event_id = state.proof_to_event_id or {}

        for proof in state.proofs:
            if selected_amount >= total_needed:
                break
            selected_proofs.append(proof)
            selected_amount += proof["amount"]
            # Track which event this proof came from
            proof_id = f"{proof['secret']}:{proof['C']}"
            if proof_id in proof_to_event_id:
                events_to_delete.add(proof_to_event_id[proof_id])

        if selected_amount < total_needed:
            raise WalletError(
                f"Insufficient balance. Need {total_needed}, have {selected_amount}"
            )

        # Convert to mint proof format
        mint_proofs: list[Proof] = []
        for p in selected_proofs:
            mint_proofs.append(self._proofdict_to_mint_proof(p))

        # Calculate change
        change_amount = selected_amount - total_needed
        change_outputs: list[BlindedMessage] = []
        change_secrets: list[str] = []
        change_blinding_factors: list[str] = []

        if change_amount > 0:
            # Create blinded messages for change
            remaining = change_amount
            keyset_id = selected_proofs[0]["id"]

            # Use the mint's currently active keyset for outputs
            keys_resp_active = await mint.get_keys()
            keysets_active = keys_resp_active.get("keysets", [])
            keyset_id_active = keysets_active[0]["id"] if keysets_active else keyset_id

            for denom in [64, 32, 16, 8, 4, 2, 1]:
                while remaining >= denom:
                    secret, r_hex, blinded_msg = self._create_blinded_message(
                        denom, keyset_id_active
                    )
                    change_outputs.append(blinded_msg)
                    change_secrets.append(secret)
                    change_blinding_factors.append(r_hex)
                    remaining -= denom

        # Execute melt
        melt_resp = await mint.melt(
            quote=quote_id,
            inputs=mint_proofs,
            outputs=change_outputs if change_outputs else None,
        )

        # Get mint public key for unblinding change
        keys_resp = await mint.get_keys()
        mint_keys = None
        if change_outputs:
            for ks in keys_resp.get("keysets", []):
                if ks["id"] == keyset_id_active:
                    keys_data: str | dict[str, str] = ks.get("keys", {})
                    if isinstance(keys_data, dict) and keys_data:
                        mint_keys = keys_data
                        break

        # Delete old token events (find which events contained the spent proofs)
        # For simplicity, assume one event per mint
        # In production, track which proofs belong to which events

        # TODO: This is incorrect - need to track which proofs belong to which
        # token events to properly delete them. Current implementation doesn't
        # maintain this mapping, violating NIP-60 requirements.

        old_token_ids = list(events_to_delete)

        # Create new token event for change
        if melt_resp.get("change") and mint_keys:
            change_proofs: list[ProofDict] = []
            for i, sig in enumerate(melt_resp["change"]):
                # Get the public key for this amount
                amount = sig["amount"]
                mint_pubkey = self._get_mint_pubkey_for_amount(mint_keys, amount)
                if not mint_pubkey:
                    raise WalletError(
                        f"Could not find mint public key for amount {amount}"
                    )

                # Unblind the signature
                C_ = PublicKey(bytes.fromhex(sig["C_"]))
                r = bytes.fromhex(change_blinding_factors[i])
                C = unblind_signature(C_, r, mint_pubkey)

                change_proofs.append(
                    ProofDict(
                        id=sig["id"],
                        amount=sig["amount"],
                        secret=change_secrets[i],
                        C=C.format(compressed=True).hex(),
                    )
                )

            token_event_id = await self.publish_token_event(
                change_proofs,
                deleted_token_ids=old_token_ids,
            )
            created_ids = [token_event_id]
        else:
            created_ids = []

        # Publish spending history
        await self.publish_spending_history(
            direction="out",
            amount=melt_quote["amount"],
            created_token_ids=created_ids,
            destroyed_token_ids=old_token_ids,
        )

    async def send(self, amount: int) -> str:
        """Send Cashu tokens of *amount* and return the serialized token."""
        # Get current wallet state with proof validation
        state = await self.fetch_wallet_state(check_proofs=True)

        # Select proofs to send
        selected_proofs: list[ProofDict] = []
        selected_amount = 0
        remaining_proofs: list[ProofDict] = []

        # Track which events contain selected proofs
        events_to_delete: set[str] = set()
        proof_to_event_id = state.proof_to_event_id or {}

        for proof in state.proofs:
            if selected_amount < amount:
                selected_proofs.append(proof)
                selected_amount += proof["amount"]
                # Track which event this proof came from
                proof_id = f"{proof['secret']}:{proof['C']}"
                if proof_id in proof_to_event_id:
                    events_to_delete.add(proof_to_event_id[proof_id])
            else:
                remaining_proofs.append(proof)

        if selected_amount < amount:
            raise WalletError(
                f"Insufficient balance. Need {amount}, have {state.balance}"
            )

        # If we selected too much, need to split
        if selected_amount > amount:
            mint = self._get_mint(self.mint_urls[0])

            # Convert to mint proofs
            mint_proofs: list[Proof] = []
            for p in selected_proofs:
                mint_proofs.append(self._proofdict_to_mint_proof(p))

            # Create outputs for exact amount and change
            outputs: list[BlindedMessage] = []
            all_secrets: list[str] = []
            all_blinding_factors: list[str] = []
            keyset_id = selected_proofs[0]["id"]

            # Use the mint's currently active keyset for outputs
            keys_resp_active = await mint.get_keys()
            keysets_active = keys_resp_active.get("keysets", [])
            keyset_id_active = keysets_active[0]["id"] if keysets_active else keyset_id

            # Outputs for sending
            send_outputs: list[BlindedMessage] = []
            send_secrets: list[str] = []
            remaining = amount
            for denom in [64, 32, 16, 8, 4, 2, 1]:
                while remaining >= denom:
                    secret, r_hex, blinded_msg = self._create_blinded_message(
                        denom, keyset_id_active
                    )
                    outputs.append(blinded_msg)
                    send_outputs.append(blinded_msg)
                    all_secrets.append(secret)
                    send_secrets.append(secret)
                    all_blinding_factors.append(r_hex)
                    remaining -= denom

            # Outputs for change
            change_amount = selected_amount - amount
            remaining = change_amount
            for denom in [64, 32, 16, 8, 4, 2, 1]:
                while remaining >= denom:
                    secret, r_hex, blinded_msg = self._create_blinded_message(
                        denom, keyset_id_active
                    )
                    outputs.append(blinded_msg)
                    all_secrets.append(secret)
                    all_blinding_factors.append(r_hex)
                    remaining -= denom

            # Swap for exact denominations
            swap_resp = await mint.swap(inputs=mint_proofs, outputs=outputs)

            # Get mint public key for unblinding
            keys_resp = await mint.get_keys()
            mint_keys = None
            for ks in keys_resp.get("keysets", []):
                if ks["id"] == keyset_id_active:
                    keys_data: str | dict[str, str] = ks.get("keys", {})
                    if isinstance(keys_data, dict) and keys_data:
                        mint_keys = keys_data
                        break

            if not mint_keys:
                raise WalletError("Could not find mint keys")

            # Separate send and change proofs
            send_proofs: list[ProofDict] = []
            change_proofs: list[ProofDict] = []

            for i, sig in enumerate(swap_resp["signatures"]):
                # Get the public key for this amount
                amount = sig["amount"]
                mint_pubkey = self._get_mint_pubkey_for_amount(mint_keys, amount)
                if not mint_pubkey:
                    raise WalletError(
                        f"Could not find mint public key for amount {amount}"
                    )

                # Unblind the signature
                C_ = PublicKey(bytes.fromhex(sig["C_"]))
                r = bytes.fromhex(all_blinding_factors[i])
                C = unblind_signature(C_, r, mint_pubkey)

                proof = ProofDict(
                    id=sig["id"],
                    amount=sig["amount"],
                    secret=all_secrets[i],
                    C=C.format(compressed=True).hex(),
                )

                if i < len(send_outputs):
                    send_proofs.append(proof)
                else:
                    change_proofs.append(proof)

            # Update remaining proofs with change proofs
            remaining_proofs = change_proofs
            selected_proofs = send_proofs

            # Also need to include any proofs we didn't select initially
            for proof in state.proofs:
                proof_id = f"{proof['secret']}:{proof['C']}"
                if (
                    proof_id in proof_to_event_id
                    and proof_to_event_id[proof_id] not in events_to_delete
                ):
                    remaining_proofs.append(proof)

        # Create Cashu token
        token = self._serialize_proofs_for_token(selected_proofs, self.mint_urls[0])

        # Delete old token events and create new one for remaining
        deleted_event_ids = list(events_to_delete)

        if remaining_proofs:
            token_event_id = await self.publish_token_event(
                remaining_proofs, deleted_token_ids=deleted_event_ids
            )
            created_ids = [token_event_id]
        else:
            # Still need to delete old events even if no remaining proofs
            for event_id in deleted_event_ids:
                await self.delete_token_event(event_id)
            created_ids = []

        # Publish spending history
        await self.publish_spending_history(
            direction="out",
            amount=amount,
            created_token_ids=created_ids,
            destroyed_token_ids=deleted_event_ids,
        )

        return token

    async def send_to_lnurl(
        self,
        lnurl: str,
        amount: int,
        *,
        fee_estimate: float = 0.01,
        max_fee: int | None = None,
    ) -> int:
        """Send funds to an LNURL address.

        Args:
            lnurl: LNURL string (can be lightning:, user@host, bech32, or direct URL)
            amount: Amount to send in the wallet's currency unit
            fee_estimate: Fee estimate as a percentage (default: 1%)
            max_fee: Maximum fee in the wallet's currency unit (optional)

        Returns:
            Amount actually paid in the wallet's currency unit

        Raises:
            WalletError: If amount is outside LNURL limits or insufficient balance
            LNURLError: If LNURL operations fail

        Example:
            # Send 1000 sats to a Lightning Address
            paid = await wallet.send_to_lnurl("user@getalby.com", 1000)
            print(f"Paid {paid} sats")
        """
        from .lnurl import get_lnurl_data, get_lnurl_invoice

        # Get LNURL data
        lnurl_data = await get_lnurl_data(lnurl)

        # Convert amounts based on currency
        if self.currency == "sat":
            amount_msat = amount * 1000
            min_sendable_sat = lnurl_data["min_sendable"] // 1000
            max_sendable_sat = lnurl_data["max_sendable"] // 1000
            unit_str = "sat"
        elif self.currency == "msat":
            amount_msat = amount
            min_sendable_sat = lnurl_data["min_sendable"]
            max_sendable_sat = lnurl_data["max_sendable"]
            unit_str = "msat"
        else:
            raise WalletError(f"Currency {self.currency} not supported for LNURL")

        # Check amount limits
        if not (
            lnurl_data["min_sendable"] <= amount_msat <= lnurl_data["max_sendable"]
        ):
            raise WalletError(
                f"Amount {amount} {unit_str} is outside LNURL limits "
                f"({min_sendable_sat} - {max_sendable_sat} {unit_str})"
            )

        # Calculate amount to request (subtract estimated fees)
        estimated_fee = int(amount * fee_estimate)
        if max_fee is not None:
            estimated_fee = min(estimated_fee, max_fee)
        estimated_fee = max(estimated_fee, 1)  # Minimum 1 unit fee

        amount_to_request = amount_msat - (
            estimated_fee * (1000 if self.currency == "sat" else 1)
        )

        # Get Lightning invoice
        bolt11_invoice, invoice_data = await get_lnurl_invoice(
            lnurl_data["callback_url"], amount_to_request
        )

        # Pay the invoice using melt
        await self.melt(bolt11_invoice)

        # Return the actual amount paid (from the invoice)
        # The melt operation handles the exact amount from the invoice
        return amount - estimated_fee

    async def roll_over_proofs(
        self,
        *,
        spent_proofs: list[ProofDict],
        unspent_proofs: list[ProofDict],
        deleted_event_ids: list[str],
    ) -> str:
        """Roll over unspent proofs after a partial spend and return new token id."""
        # Delete old token events
        for event_id in deleted_event_ids:
            await self.delete_token_event(event_id)

        # Create new token event with unspent proofs
        return await self.publish_token_event(
            unspent_proofs,
            deleted_token_ids=deleted_event_ids,
        )

    # ─────────────────────────────── Cleanup ──────────────────────────────────

    async def aclose(self) -> None:
        """Close underlying HTTP clients."""
        await self.mint_client.aclose()

        # Close relay connections
        for relay in self.relay_instances:
            await relay.disconnect()

        # Close mint clients
        for mint in self.mints.values():
            await mint.aclose()

    # ───────────────────────── Async context manager ──────────────────────────

    async def __aenter__(self) -> "Wallet":
        """Enter async context and auto-initialize wallet."""
        try:
            # Try to fetch existing wallet state with proof validation
            await self.fetch_wallet_state(check_proofs=True)
        except Exception:
            # If no wallet exists or fetch fails, create a new wallet event
            try:
                await self.create_wallet_event()
            except Exception:
                # If we can't create a wallet event, that's okay -
                # user might just want to do offline operations
                pass
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: D401  (simple return)
        await self.aclose()

    # ───────────────────────── Factory Methods ────────────────────────────────

    @classmethod
    async def create(
        cls,
        nsec: str,
        *,
        mint_urls: list[str] | None = None,
        currency: Literal["sat", "msat", "usd"] = "sat",
        wallet_privkey: str | None = None,
        relays: list[str] | None = None,
        auto_init: bool = True,
    ) -> "Wallet":
        """Create and optionally initialize a wallet with network operations.

        Args:
            nsec: Nostr private key
            mint_urls: Cashu mint URLs
            currency: Currency unit
            wallet_privkey: Private key for P2PK operations
            relays: Nostr relay URLs
            auto_init: If True, create wallet event and fetch state

        Returns:
            Initialized wallet instance
        """
        wallet = cls(
            nsec=nsec,
            mint_urls=mint_urls,
            currency=currency,
            wallet_privkey=wallet_privkey,
            relays=relays,
        )

        if auto_init:
            try:
                # Try to fetch existing state first with proof validation
                await wallet.fetch_wallet_state(check_proofs=True)
            except Exception:
                # If no wallet exists, create one
                await wallet.create_wallet_event()

        return wallet

    def _proofdict_to_mint_proof(self, proof_dict: ProofDict) -> Proof:
        """Convert ProofDict (with base64 secret) to Proof (with hex secret) for mint.

        NIP-60 stores secrets as base64, but Cashu protocol expects hex.
        """
        # Decode base64 secret to get raw bytes
        try:
            secret_bytes = base64.b64decode(proof_dict["secret"])
            secret_hex = secret_bytes.hex()
        except Exception:
            # Fallback: assume it's already hex (backwards compatibility)
            secret_hex = proof_dict["secret"]

        return Proof(
            id=proof_dict["id"],
            amount=proof_dict["amount"],
            secret=secret_hex,  # Mint expects hex
            C=proof_dict["C"],
        )


class TempWallet(Wallet):
    """Temporary wallet that generates a new random private key without storing it.

    This wallet creates a new random Nostr private key on initialization and
    operates entirely in memory. The private key is not stored or persisted
    anywhere, making it suitable for ephemeral operations.
    """

    def __init__(
        self,
        *,
        mint_urls: list[str] | None = None,
        currency: Literal["sat", "msat", "usd"] = "sat",
        wallet_privkey: str | None = None,
        relays: list[str] | None = None,
    ) -> None:
        """Initialize temporary wallet with a new random private key.

        Args:
            mint_urls: Cashu mint URLs (defaults to minibits mint)
            currency: Currency unit (sat, msat, or usd)
            wallet_privkey: Private key for P2PK operations (generated if not provided)
            relays: Nostr relay URLs to use
        """
        # Generate a new random private key
        temp_privkey = PrivateKey()
        temp_nsec = self._encode_nsec(temp_privkey)

        # Initialize parent with generated nsec
        super().__init__(
            nsec=temp_nsec,
            mint_urls=mint_urls,
            currency=currency,
            wallet_privkey=wallet_privkey,
            relays=relays,
        )

    def _encode_nsec(self, privkey: PrivateKey) -> str:
        """Encode private key as nsec (bech32) format.

        Args:
            privkey: The private key to encode

        Returns:
            nsec-encoded private key string
        """
        # Try to use bech32 encoding if available
        if bech32_decode is not None and convertbits is not None:
            from bech32 import bech32_encode  # type: ignore

            # Convert private key bytes to 5-bit groups for bech32
            key_bytes = privkey.secret
            converted = convertbits(key_bytes, 8, 5, pad=True)
            if converted is not None:
                encoded = bech32_encode("nsec", converted)
                if encoded:
                    return encoded

        # Fallback to hex encoding with nsec prefix
        return f"nsec_{privkey.to_hex()}"

    @classmethod
    async def create(  # type: ignore[override]
        cls,
        *,
        mint_urls: list[str] | None = None,
        currency: Literal["sat", "msat", "usd"] = "sat",
        wallet_privkey: str | None = None,
        relays: list[str] | None = None,
        auto_init: bool = True,
    ) -> "TempWallet":
        """Create and optionally initialize a temporary wallet.

        Args:
            mint_urls: Cashu mint URLs
            currency: Currency unit
            wallet_privkey: Private key for P2PK operations
            relays: Nostr relay URLs
            auto_init: If True, create wallet event and fetch state

        Returns:
            Initialized temporary wallet instance
        """
        wallet = cls(
            mint_urls=mint_urls,
            currency=currency,
            wallet_privkey=wallet_privkey,
            relays=relays,
        )

        if auto_init:
            try:
                # Try to fetch existing state first with proof validation
                await wallet.fetch_wallet_state(check_proofs=True)
            except Exception:
                # If no wallet exists, create one
                await wallet.create_wallet_event()

        return wallet


async def redeem_to_lnurl(token: str, lnurl: str) -> int:
    """Redeem a token to an LNURL address and return the amount redeemed."""
    async with TempWallet() as wallet:
        amount, _ = await wallet.redeem(token)
        await wallet.send_to_lnurl(lnurl, amount)
        return amount
