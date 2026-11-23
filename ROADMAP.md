# RAGForge roadmap

## Vision

Build a reusable, extensible AI knowledge management platform that enables developers, teams and organizations to manage knowledge bases and integrate source-grounded Q&A into their own applications and websites.

## Current foundation (planned v0.1.0)

Multi-user authentication and document ownership, asynchronous PDF ingestion, semantic retrieval, stateless and conversational Q&A, persistent checkpoints, local Docker installation, CI and evaluation tooling. Organization-level multi-tenancy and embeddable guest access are not implemented yet.

## Proposed milestones

| Milestone | Direction | Acceptance goals |
|---|---|---|
| v0.2.0 | Organizations and tenant isolation | Membership roles, tenant-scoped data access, cross-tenant isolation tests |
| v0.3.0 | Knowledge bases | Multiple documents per knowledge base, scoped retrieval, lifecycle management |
| v0.4.0 | Embeddable Q&A | Widget integration, scoped credentials, allowed origins |
| v0.5.0 | Guest sessions | Expiring sessions, abuse controls, quotas and tenant-scoped access |
| v0.6.0 | Data sources | Additional formats and connectors, safe ingestion and retries |
| v0.7.0 | Administration | Usage metrics, job visibility and operational controls |
| v1.0.0 | Stable platform | Documented API compatibility, security review, deployment and recovery guidance |

## Cross-cutting priorities

Security, tenant isolation, testing, evaluation quality, observability, accessibility and developer experience should evolve with every milestone. Public deployment, continuous deployment and live demonstrations are planned separately after deployment prerequisites are met.

This roadmap is directional, not a delivery commitment. Priorities and version numbers may change based on feedback and engineering constraints. Propose improvements through GitHub issues or discussions.
