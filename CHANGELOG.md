
# Changelog

All notable changes to RAGForge will be documented in this file.

The format is based on Keep a Changelog, and this project
adheres to Semantic Versioning.

## [Unreleased]

## [0.1.0] - 2026-11-24

Initial public release of RAGForge.

### Added

- Versioned FastAPI REST API with interactive OpenAPI documentation.
- JWT-based authentication and Argon2 password hashing.
- User-scoped document and conversation access.
- Asynchronous PDF ingestion using database-backed background jobs.
- Job leasing, bounded retries, and generation-aware indexing.
- Local sentence-transformer embeddings.
- ChromaDB-powered semantic document retrieval.
- Groq-powered document-grounded question answering.
- Page-level source citations and insufficient-context handling.
- LangGraph-powered conversational question answering.
- Context-aware follow-up question rewriting.
- PostgreSQL-backed persistent conversation checkpoints.
- Conversation concurrency protection using advisory locks.
- Docker Compose development and testing environments.
- Alembic database migrations.
- Structured application logging and health endpoints.
- Automated unit and integration tests.
- Optional LangSmith tracing and evaluation workflows.
- GitHub Actions continuous integration.
- Architecture documentation and an end-to-end demo guide.
- MIT License, contribution guidelines, security policy,
  community standards, and GitHub contribution templates.
- Long-term product development roadmap.

### Known limitations

- Ingestion is limited to text-based PDF documents.
- Conversations are scoped to individual documents.
- Organization-level multi-tenancy is not yet implemented.
- Embeddable widgets and guest conversations are planned.
- Local file storage is the supported end-to-end storage option.
- Public cloud deployment and continuous deployment are pending.
- Additional operational and security hardening is required
  before public production deployment.

[Unreleased]: https://github.com/mehmood22/ragforge/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/mehmood22/ragforge/releases/tag/v0.1.0
