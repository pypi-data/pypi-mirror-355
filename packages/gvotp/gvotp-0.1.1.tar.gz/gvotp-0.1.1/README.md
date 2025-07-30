# GVOTP

A lightweight in-memory OTP (One-Time Password) generator and verifier with external record support.

## Installation

```bash
pip install gvotp
```

---
## 🚀 Usage
```commandline
from gvotp import GVOTP

otp_manager = GVOTP()

# Generate an OTP
result = otp_manager.generate_otp("email", "user@example.com")

# Access the raw OTP (to send via email, SMS, etc.)
otp = result["otp"]

# (Optional) Use result["otp_record"] if you prefer storing OTPs externally
otp_doc = result["otp_record"]
# Example structure:
# {
#     'kind': 'email',
#     'receiver': 'user@example.com',
#     'otp_hash': '...',
#     'attempts': 0,
#     'create_time': 1750093088,
#     'ttl': 900
# }

# ✅ In-memory OTP verification
otp_manager.verify_otp("email", "user@example.com", otp)

# ✅ External document verification (if OTP record is stored externally)
otp_manager.verify_otp("email", "user@example.com", otp, document=otp_doc)

```
📌 Note
- OTPs expire after the configured TTL (default: 15 minutes).

- Maximum 5 failed attempts are allowed per OTP.

- Once an OTP is successfully verified, it is deleted from in-memory store automatically.

- If using external storage (like a database), you must manage record deletion post-verification.

