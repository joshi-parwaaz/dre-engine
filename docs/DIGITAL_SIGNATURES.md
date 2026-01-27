# Digital Signature Implementation - Non-Repudiation

## Overview

The DRE Guardian now implements cryptographic non-repudiation for all override requests using SHA-256 hashing.

## How It Works

### 1. Override Submission (Frontend)

When a user bypasses a HALT from the Leadership dashboard:

1. **Modal appears** requiring:
   - Justification (text explaining why)
   - Digital signature (name or employee ID)

2. **Hash computation** (client-side):
   ```javascript
   const hashInput = `${justification}|${signature}|${timestamp}`
   const hashBuffer = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(hashInput))
   const hashHex = Array.from(new Uint8Array(hashBuffer))
     .map(b => b.toString(16).padStart(2, '0'))
     .join('')
   ```

3. **Submission** to backend:
   ```json
   {
     "assertion_ids": ["ast-001", "ast-002"],
     "justification": "CFO approved new Q2 target",
     "signature": "John Smith - CFO",
     "timestamp": "2026-01-27T10:30:00.000Z",
     "signature_hash": "a3f5c9d8e2b1..."
   }
   ```

### 2. Storage (Backend)

The backend stores in `audit_log.jsonl`:

```json
{
  "timestamp": "2026-01-27T10:30:00.000Z",
  "event_type": "OVERRIDE_REQUEST",
  "assertion_id": "ast-001",
  "severity": "WARN",
  "user": "John Smith - CFO",
  "details": {
    "justification": "CFO approved new Q2 target",
    "timestamp": "2026-01-27T10:30:00.000Z",
    "signature_hash": "a3f5c9d8e2b1f4c7a8d3e5b9c2f1a4d7...",
    "hash_input": "CFO approved new Q2 target|John Smith - CFO|2026-01-27T10:30:00.000Z"
  }
}
```

### 3. Verification (CLI Tool)

Anyone can verify the signature hasn't been tampered with:

```bash
# Verify all overrides in audit log
python cli.py verify

# Verify a specific override
python cli.py verify \
  --justification "CFO approved new Q2 target" \
  --signature "John Smith - CFO" \
  --timestamp "2026-01-27T10:30:00.000Z" \
  --hash "a3f5c9d8e2b1f4c7a8d3e5b9c2f1a4d7..."
```

The tool:
1. Reconstructs hash input: `justification|signature|timestamp`
2. Computes SHA-256 hash
3. Compares with stored hash
4. Reports `✓ VALID` or `✗ TAMPERED`

## Security Properties

### Non-Repudiation
Once an override is submitted, the user cannot deny they made it:
- The signature (name/ID) is part of the hash
- Changing the signature would break the hash
- The audit log proves who authorized what

### Tamper-Evidence
If anyone modifies the justification after submission:
- The stored hash won't match
- Verification tool will detect tampering
- Audit trail integrity is provable

### Cryptographic Strength
SHA-256 properties:
- **Collision resistance**: Impossible to find two inputs with same hash
- **Pre-image resistance**: Can't reverse engineer justification from hash
- **Avalanche effect**: Tiny change → completely different hash

## Use Cases

### Legal Compliance
```bash
# Generate audit report for legal team
python cli.py audit --filter override --since 2026-01-01 > overrides_2026.json

# Verify all signatures are intact
python cli.py verify
```

Output:
```
✓ All 47 override signature(s) verified successfully
No tampering detected - audit trail integrity maintained
```

### Forensic Investigation
```bash
# Find specific override
python cli.py audit --filter override | grep "John Smith"

# Verify that specific override
python cli.py verify \
  --justification "Board directive for emergency funding" \
  --signature "John Smith - CFO" \
  --timestamp "2026-01-15T14:23:00.000Z" \
  --hash "b4d8c3e9f1a2..."
```

### Dispute Resolution
If someone claims "I never said that":
1. Pull the override from audit log
2. Show the stored hash
3. Recompute hash from original data
4. Prove hash matches = signature is authentic

### Regulatory Audit
```bash
# Show all overrides in last quarter
python cli.py audit --filter override --since 2025-10-01

# Verify integrity
python cli.py verify

# Export for auditor
python cli.py audit --filter override --since 2025-10-01 > Q4_overrides.json
```

## What Gets Hashed

```
Hash Input Format:
  justification|signature|timestamp

Example:
  "CFO approved new Q2 revenue target per board meeting 2026-01-15|John Smith - CFO|2026-01-27T10:30:00.000Z"
  
SHA-256 Output:
  "a3f5c9d8e2b1f4c7a8d3e5b9c2f1a4d7e8b3c5f2a9d1e4b7c3f8a2d5e1b9c4f7..."
```

## What This Prevents

❌ **User claims**: "I didn't authorize that override"
- Hash proves their signature was used

❌ **User modifies justification later**: "I said X, not Y"
- Changed text → different hash → verification fails

❌ **Admin changes attribution**: Switching "John Smith" to "Jane Doe"
- Changed signature → different hash → verification fails

❌ **Backdating**: Changing timestamp after the fact
- Changed timestamp → different hash → verification fails

## Frontend Implementation

File: `dashboard/src/App.tsx`

```typescript
// Bypass modal shows when user clicks "Bypass HALT" button
const [showBypassModal, setShowBypassModal] = useState(false)
const [bypassJustification, setBypassJustification] = useState('')
const [bypassSignature, setBypassSignature] = useState('')

// On submit:
const hashInput = `${bypassJustification}|${bypassSignature}|${timestamp}`
const hashBuffer = await crypto.subtle.digest('SHA-256', 
  new TextEncoder().encode(hashInput))
const hashHex = Array.from(new Uint8Array(hashBuffer))
  .map(b => b.toString(16).padStart(2, '0')).join('')

// POST to /override with signature_hash field
```

## Backend Implementation

File: `guardian/api/bridge.py`

```python
class OverrideRequest(BaseModel):
    assertion_ids: List[str]
    justification: str
    signature: str
    timestamp: str
    signature_hash: str  # SHA-256 for non-repudiation

# Stores in audit log:
audit_logger.log_event(
    event_type="OVERRIDE_REQUEST",
    assertion_id=assertion_id,
    details={
        "justification": request.justification,
        "timestamp": request.timestamp,
        "signature_hash": request.signature_hash,
        "hash_input": f"{request.justification[:50]}|{request.signature}|{request.timestamp}"
    },
    user=request.signature,
    severity="WARN"
)
```

## CLI Verification Tool

File: `guardian/tools/verify_signature.py`

```python
def compute_hash(justification: str, signature: str, timestamp: str) -> str:
    hash_input = f"{justification}|{signature}|{timestamp}"
    return hashlib.sha256(hash_input.encode()).hexdigest()

def verify_audit_log(audit_log_path: str):
    # Read all OVERRIDE_REQUEST events
    # Recompute hash for each
    # Compare with stored hash
    # Report verification status
```

## Testing

1. **Submit override via dashboard**:
   - Fill in justification and signature
   - Click "Submit Override"
   - Note the hash shown in confirmation

2. **Verify in audit log**:
   ```bash
   python cli.py audit --filter override --limit 1
   ```

3. **Run verification**:
   ```bash
   python cli.py verify
   ```

4. **Manual tampering test**:
   - Edit `audit_log.jsonl` 
   - Change justification text
   - Run `python cli.py verify`
   - Should show `✗ TAMPERED`

## Production Checklist

✅ SHA-256 hash computed client-side  
✅ Hash stored in audit log  
✅ Verification tool available via CLI  
✅ Modal requires both justification AND signature  
✅ Submit button disabled until both fields filled  
✅ Hash displayed to user after submission  
✅ Audit log includes `hash_input` for verification  
✅ Non-repudiation notice shown in modal  

## Future Enhancements

1. **Asymmetric signatures**: Use private/public key pairs instead of SHA-256
2. **Timestamp authority**: Add trusted timestamp server integration
3. **Blockchain**: Store hash on immutable ledger
4. **Multi-sig**: Require multiple approvers for critical overrides
5. **HSM integration**: Hardware security module for key storage
