# How the Audit Chain Works

ShadowAudit's audit log is tamper-evident by design. Every entry is cryptographically linked to the previous one via a hash chain, making it impossible to alter or delete a past decision without invalidating all subsequent entries.

## Hash Chain Mechanics

Each audit entry contains:

- `prev_hash`: SHA-256 of the previous entry's `entry_hash` (empty string for the genesis entry)
- `entry_hash`: SHA-256 of all entry fields concatenated with `prev_hash`

The hash is computed as:

```
entry_hash = SHA-256( canonical_json(entry_fields) + prev_hash )
```

Where `canonical_json` sorts keys, strips whitespace, and uses deterministic serialization.

## Verification

Verify any SQLite audit log database:

```bash
shadowaudit verify --audit-log ./audit.db
```

This re-computes every `entry_hash` and checks `prev_hash` linkage. If any row has been modified, deleted, or reordered, verification fails with a detailed error message.

## Why This Matters for Compliance

- **EU AI Act Article 12** requires tamper-evident logs for high-risk AI systems.
- **SOX 404** requires append-only decision logs for internal controls.
- A standard SQLite table can be edited by anyone with file access. The hash chain makes tampering detectable.

## Limitations

- The hash chain proves *integrity*, not *authenticity*. An attacker with file access can delete the entire database.
- For authenticity, combine with Ed25519 signing (Week 7b) and offline key storage.
- For availability, back up the audit database to immutable storage (S3 Object Lock, WORM tape).
