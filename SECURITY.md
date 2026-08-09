# Security Policy

Do not open a public issue for credential exposure, unauthorized order execution, or another
security-sensitive defect. Report it privately through GitHub's repository security advisory
feature.

Never commit broker passwords, investor passwords, API tokens, account numbers, or `.env` files.
Revoke and rotate a credential immediately if it is exposed. Trading execution must fail closed:
stale data, invalid configuration, disconnected terminals, or breached risk limits must prevent
new orders.

