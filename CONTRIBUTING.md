# Contributing to RAGForge

RAGForge aims to become an extensible knowledge management and embeddable Q&A platform. Contributions to code, tests, documentation and evaluations are welcome.

## Getting started

1. Discuss substantial changes in an issue before implementation.
2. Fork the repository (external contributors), clone it and create a branch from `main`.
3. Follow the [README](README.md) for local setup, migrations and Docker services. Read [Architecture](docs/ARCHITECTURE.md) before changing core workflows.
4. Keep credentials in local environment files; never commit them.

## Engineering standards

- Keep routes thin, business logic in services and persistence in repositories where appropriate.
- Prefer explicit dependencies, typed interfaces, small cohesive modules and consistent API contracts.
- Preserve ownership checks, document generation isolation and conversation concurrency guarantees.
- Add Alembic migrations for relational schema changes; do not edit previously released migrations.
- Add regression tests for bug fixes and positive and negative tests for features.
- For AI changes, test abstention, citation behavior and retrieval isolation; use synthetic data and document evaluation limitations.

## Quality checks

Install development dependencies and run the static checks from the repository root:

```sh
uv sync --locked --group dev
uv run ruff check .
uv run ruff format --check .
uv run mypy src
```

Follow the README's isolated Docker test instructions for integration tests. Do not run destructive tests against a database containing real user data. Run relevant evaluations for retrieval or prompt changes, using your own credentials and sample documents. CI is the authoritative merge gate.

## Pull requests

Use a focused branch, such as `fix/ingestion-retry` or `feat/knowledge-bases`. Prefer descriptive commits (`fix:`, `feat:`, `docs:`, `test:`). Explain the problem, solution, tests and any compatibility or security implications. Update documentation and changelog when appropriate. Do not include unrelated changes or secrets. Wait for CI to pass before merging.

By submitting a contribution, you agree that it may be distributed under the project's [MIT License](LICENSE). Only submit material you have permission to contribute.

See the [Code of Conduct](CODE_OF_CONDUCT.md) and [Security Policy](SECURITY.md).
