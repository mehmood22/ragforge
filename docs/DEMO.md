# RAGForge demo walkthrough

Use the synthetic `sample-telecom-policy.pdf` in this directory. It contains fictional policies, not real customer information. Start the stack using the README and open http://localhost:8000/docs.

## Swagger workflow

1. Register with `POST /api/v1/auth/register`:
   ```json
   {"email":"demo@example.com","password":"Demo-local-password-123"}
   ```
2. Login with the same JSON at `/api/v1/auth/login`. Copy `data.access_token` and paste it into Swagger's Authorize dialog.
3. Upload the sample PDF via `/api/v1/uploads/pdf`, field `file`. Save the returned document and job UUIDs.
4. Poll `/api/v1/ingestion-jobs/{job_id}` until `completed`. Confirm document status `indexed` at `/api/v1/documents/{document_id}`.
5. Call `/api/v1/retrieval/search` with `{"document_id":"YOUR_UUID","query":"autopay invoice charge","top_k":5}`.
6. Call `/api/v1/qa/ask` with `{"document_id":"YOUR_UUID","question":"When are autopay customers charged?"}`. Expected fact: 14 days. Inspect the page-level sources.
7. Ask `What is the company's revenue in 2040?` using the same endpoint. Expected status: `insufficient_context`.
8. Generate a conversation UUID with PowerShell `[guid]::NewGuid().ToString()` or Linux/macOS `uuidgen`. Call `/api/v1/conversations/ask` with:
   ```json
   {"document_id":"YOUR_DOCUMENT_UUID","conversation_id":"YOUR_CONVERSATION_UUID","question":"How long are recent SIM swaps monitored?"}
   ```
   Ask `Why is that monitoring applied?` with the same IDs. Retrieve history using `/api/v1/conversations/{conversation_id}/messages`.
9. Register and login as a second user. Attempt to fetch the first user's document and job; access should be denied. Never include tokens in screenshots.

Expected outcomes are demo checks, not recorded execution results. LLM behavior can vary. If a check fails, inspect logs and report it rather than treating it as passed.

## Suggested recording (90–120 seconds)

- 0–15 s: GitHub README, architecture and passing CI.
- 15–35 s: Docker services and Swagger; upload sample PDF.
- 35–55 s: Completed job and indexed document.
- 55–80 s: Grounded answer with citations and unsupported question.
- 80–105 s: Follow-up conversation and history.
- 105–120 s: Explain ownership checks and future deployment.

Record only real outputs. Hide secrets, tokens and personal data. If ingestion takes longer, cut the waiting period and label the edit.
