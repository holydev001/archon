# Contributing

## Branch model

- `main` is the release branch. It accepts pull requests from `dev` only.
- `dev` is the integration branch. Direct commits and direct merges are prohibited.
- Work is developed on short-lived branches such as `feat/core-engine`, `fix/order-sizing`,
  `docs/architecture`, or `chore/dependencies`.
- Do not use personal or tool-specific prefixes in branch names.

## Pull request flow

1. Branch from the latest `dev`.
2. Make focused commits using Conventional Commit prefixes.
3. Run `python -m ruff check .` and `python -m pytest -q`.
4. Open a pull request into `dev` and complete the safety checklist.
5. Merge only after required checks and review pass.
6. Promote a release using a pull request from `dev` into `main`.

Execution-related changes must remain demo-only until an explicitly reviewed milestone authorizes
otherwise. Never commit broker credentials, account identifiers, private market data, or secrets.

