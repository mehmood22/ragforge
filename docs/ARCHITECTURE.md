# Architecture and design decisions

RAGForge separates protected document management from retrieval and AI operations. Registration and login are public; protected routes authenticate the JWT and enforce resource ownership where applicable. PostgreSQL is the system of record, ChromaDB is the vector index, and the independent worker handles ingestion. These are separate workflows, not a single pipeline.

## 1. Document upload and asynchronous indexing

```mermaid
sequenceDiagram
    actor U as Client
    participant A as FastAPI / Upload service
    participant S as PDF storage
    participant P as PostgreSQL
    participant W as Ingestion worker
    participant V as ChromaDB
    U->>A: Upload PDF with JWT
    Note over A: Authenticate and validate PDF
    A->>S: Store original file
    A->>P: Persist document and pending job
    A-->>U: 202 Accepted + document/job IDs
    W->>P: Claim job with lease
    W->>S: Read PDF
    Note over W: Extract text, chunk and embed locally
    W->>V: Index chunks and vectors with generation metadata
    W->>P: Finalize job and active generation
```

The worker polls independently of the HTTP request. Leases and bounded retries support recovery. Generation-aware retrieval avoids incomplete indexing generations; this is not an exactly-once guarantee. No generative LLM is needed for ingestion.

## 2. Document metadata and job status

```mermaid
sequenceDiagram
    actor U as Client
    participant A as FastAPI
    participant P as PostgreSQL
    U->>A: List documents / Get document / Get job status
    Note over A: Authenticate JWT
    A->>P: Ownership-scoped repository lookup
    P-->>A: Metadata or status
    A-->>U: JSON response
```

No vector search or LLM is needed. Document viewing here means metadata, not downloading the original PDF.

## 3. Semantic search

```mermaid
sequenceDiagram
    actor U as Client
    participant A as FastAPI
    participant P as PostgreSQL
    participant R as Retrieval service
    participant E as Local embedding model
    participant V as ChromaDB
    U->>A: POST /retrieval/search
    A->>P: Verify document ownership
    A->>R: Search document
    R->>P: Check indexed status and active generation
    R->>E: Embed query locally
    R->>V: Similarity search scoped to document and generation
    V-->>R: Matching chunks and scores
    R-->>A: Filtered chunks and metadata
    A-->>U: JSON response
```

The configured top-k and minimum relevance score constrain retrieval. No generative LLM is called.

## 4. Stateless question answering

```mermaid
sequenceDiagram
    actor U as Client
    participant A as FastAPI
    participant P as PostgreSQL
    participant Q as QA service
    participant R as Retrieval service
    participant V as ChromaDB
    participant L as Groq
    U->>A: POST /qa/ask
    A->>P: Verify document ownership
    A->>Q: Ask question
    Q->>R: Retrieve context
    R->>P: Check readiness and active generation
    Note over R: Embed query locally
    R->>V: Scoped similarity search
    V-->>R: Relevant chunks
    R-->>Q: Filtered chunks
    alt Usable context exists
        Q->>L: Grounded prompt with document excerpts
        L-->>Q: Structured answer
        Note over Q: Validate answer and citations
    else Insufficient context
        Note over Q: Return abstention without answer-generation call
    end
    Q-->>A: Result and sources
    A-->>U: JSON response
```

Retrieval precedes generation. This endpoint does not persist conversational history.

## 5. Conversational RAG

```mermaid
sequenceDiagram
    actor U as Client
    participant A as FastAPI
    participant P as PostgreSQL
    participant G as LangGraph
    participant R as Retrieval service
    participant V as ChromaDB
    participant L as Groq
    U->>A: POST /conversations/ask
    A->>P: Verify ownership and acquire advisory lock
    A->>P: Create or validate conversation metadata
    A->>G: Read state and invoke scoped thread
    G->>P: Load checkpoint
    opt Previous messages exist
        G->>L: Rewrite follow-up using up to 10 prior messages
        L-->>G: Standalone question
    end
    G->>R: Retrieve using standalone question
    R->>P: Check indexed status and generation
    Note over R: Embed query locally
    R->>V: Scoped similarity search
    V-->>R: Matching chunks
    R-->>G: Relevant context
    alt Usable context exists
        G->>L: Generate grounded structured answer via QA service
        L-->>G: Answer
        Note over G: QA service validates answer and sources
    else Insufficient context
        Note over G: Produce abstention
    end
    G->>P: Persist graph state through checkpoints
    G-->>A: Result and sources
    A->>P: Update conversation metadata and release lock
    A-->>U: JSON response
```

Checkpoint writes can occur throughout graph execution; the diagram summarizes persistence. The first question bypasses rewriting. Follow-ups may call Groq before retrieval, then again for answer generation if context exists. Conversation list and history requests read PostgreSQL without running retrieval or generation.

## 6. Storage responsibilities

| Component | Responsibility |
|---|---|
| PostgreSQL | Users, document metadata, ingestion jobs, conversation metadata and LangGraph checkpoints |
| ChromaDB | Indexed text chunks, embeddings, document/generation identifiers and page/chunk metadata |
| Local PDF storage | Original PDFs shared between API and worker |
| Local embedding model | Document and query vectors; model cache on shared volume |
| Groq | Follow-up rewriting and grounded answer generation; not the application database |

## Trade-offs

| Decision | Benefit | Cost / limitation |
|---|---|---|
| PostgreSQL-backed queue | Fewer infrastructure dependencies | Polling and lease management |
| Separate worker | Slow PDF processing outside request lifecycle | Additional process and shared storage |
| Local embeddings | No external embedding API needed | CPU/RAM and model download |
| Separate vector database | Dedicated semantic retrieval | Additional service and consistency concerns |
| PostgreSQL checkpoints | Conversation history survives API restarts | Database lifecycle and concurrency management |
| Service/repository boundaries | Testable business logic and persistence separation | More modules than a simple script |
| Docker Compose | Reproducible local multi-service environment | Not high availability or managed orchestration |

The current trust boundary is individual user ownership, not organization-level tenancy. External Groq requests contain relevant document excerpts; optional tracing/evaluation can transmit additional data. Public deployment requires further operational and security controls.
