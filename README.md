# RAGVault

**RAGVault is a permission-aware Retrieval-Augmented Generation (RAG) system that combines semantic search with access control to generate grounded answers from authorized knowledge sources.**

Unlike a basic RAG pipeline, RAGVault enforces user and tenant permissions before retrieved content is passed to the language model, helping prevent unauthorized information disclosure.

## Features

- **Document ingestion and retrieval** — ingest company documents, perform vector search, and generate source-cited answers.
- **Tenant isolation** — scope document retrieval to the appropriate tenant.
- **Role-based access control (RBAC)** — enforce user roles and document permissions.
- **Access requests** — allow users to request access to restricted documents.
- **Audit timeline and security events** — review relevant actions and access decisions.
- **Chat history** — revisit conversations from the user workspace.
- **Admin dashboard** — manage users, roles, documents, and access requests.
- **Security leakage checks** — test permission boundaries and unauthorized retrieval scenarios.
- **RAGAS evaluation** — evaluate answer and retrieval quality using a repeatable question set.

## Architecture

```text
User / Admin
     |
     v
Web UI (localhost:3000)
     |
     v
FastAPI backend (localhost:8000)
     |
     +---- Authentication and authorization
     |
     +---- Permission-aware retrieval ------> Qdrant
     |                                          |
     |                                   Filtered document chunks
     |
     +---- Application metadata / audit ----> PostgreSQL
     |
     +---- Authorized context --------------> LLM provider
                                                |
                                                v
                                         Answer + sources
```

> **Security principle:** Only authorized document content should be included in the context sent to the language model. RAGAS quality scores do not replace authorization and security tests.

## Technology stack

| Component | Technology | Purpose |
| --- | --- | --- |
| Backend API | FastAPI | API endpoints and RAG orchestration |
| Relational database | PostgreSQL | Application metadata and related records |
| Vector database | Qdrant | Vector search with payload filters |
| Authentication | JWT | Represent and validate authenticated identity |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2`* | Embed document chunks and user queries |
| LLM provider | Configurable; saved evaluation used `openai/gpt-oss-120b` | Generate answers from authorized context |
| Evaluation | RAGAS 0.4.3 | Assess retrieval and answer quality |
| Evaluator model | `openai/gpt-oss-20b`* | Score evaluation samples |
| Local services | Docker Compose | Run the application and dependencies |

\* Confirm the active embedding and evaluator models in your environment before reproducing an evaluation.

## Run locally with Docker

### Prerequisites

- Docker Desktop with Docker Compose, or Docker Engine with the Compose plugin
- An API key for the LLM provider configured by the project
- Git, if cloning the repository

### 1. Configure environment variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Open `.env` and configure at least:

- `JWT_SECRET_KEY` — use a strong, unique secret.
- `POSTGRES_PASSWORD` — use a strong database password.
- The LLM provider, model, and corresponding API key required by your configuration.

Variable names can depend on the current `.env.example`; use that file as the source of truth.

**Never commit `.env`, real credentials, JWT secrets, or API keys to GitHub.**

### 2. Build and start the application

From the repository root:

```powershell
docker compose up --build -d
```

Check service status:

```powershell
docker compose ps
```

Inspect logs if a service fails to start:

```powershell
docker compose logs --tail=100
```

### 3. Open the application

- **Web UI:** [http://localhost:3000](http://localhost:3000)
- **API base URL:** [http://localhost:8000](http://localhost:8000)
- **Health check:** [http://localhost:8000/health](http://localhost:8000/health)

Sign in using an account created by an administrator. Do not assume a default admin account exists unless the repository setup explicitly creates one.

### 4. Stop the application

```powershell
docker compose down
```

This stops and removes the Compose containers and network. It does not normally delete named volumes. Review the Compose file before using volume-removal options, since those can delete local database data.

## How the RAG workflow works

1. **Ingest documents:** Load supported documents and extract their text.
2. **Chunk the text:** Split content into passages suitable for retrieval.
3. **Create embeddings:** Convert chunks into vectors using the configured embedding model.
4. **Index content and metadata:** Store vectors and filterable metadata in the vector database.
5. **Authenticate the user:** Validate request identity on the backend.
6. **Apply access rules:** Resolve tenant and document permissions before using retrieved content.
7. **Retrieve relevant chunks:** Search the vector index with permission-aware filters.
8. **Validate retrieval results:** Ensure each candidate is still authorized before adding it to the prompt.
9. **Generate an answer:** Send only authorized context to the configured LLM.
10. **Return and audit:** Return the answer and permitted source details, and record relevant events as implemented.

## RAGAS evaluation

The saved **v2 evaluation** used 25 questions, permission-aware retrieval with `top-k=5`, answers generated by `openai/gpt-oss-120b`, and RAGAS 0.4.3 metrics scored using `openai/gpt-oss-20b`.

Mean scores use a **0–1 scale**:

| Metric | Average | Configured target | Result |
| --- | ---: | ---: | --- |
| Faithfulness | 0.797 | 0.70 | Meets target |
| Answer relevancy | 0.731 | 0.70 | Meets target |
| Context precision | 0.799 | 0.70 | Meets target |
| Context recall | 0.868 | 0.70 | Meets target |
| Context entity recall | 0.696 | 0.70 | Slightly below target |
| Noise sensitivity (lower is better) | 0.128 | ≤ 0.20 | Meets target |

Context entity recall is slightly below the configured 0.70 target; the other listed metric averages meet their configured targets. These scores are benchmark indicators, not a guarantee of production quality or a substitute for authorization and security tests.

### Evaluation artifacts

- [Saved v2 RAGAS results](./evaluation/ragas_results_v2.json)
- [RAGAS evaluation report (PDF)](./evaluation/reports/ragvault_ragas_evaluation_report_v2.pdf)

## Run tests

Run the backend test suite inside the running backend container:

```powershell
docker compose exec backend pytest -q tests
```

Run focused UI API tests:

```powershell
docker compose exec backend pytest -q tests/ui_api
```

Run these commands from the repository root after starting the relevant services.

### Important security test cases

- An employee cannot retrieve an Admin-only document.
- A user cannot access another tenant's documents by changing request identifiers.
- Unauthorized chunks never reach the LLM context.
- Access requests are visible to the correct requester and can only be decided by authorized approvers.
- Revoked access is enforced even if stale vector metadata remains.
- Chat history is accessible only to its authorized owner.
- Error responses and audit logs do not expose credentials or restricted document content.

## Security notes

- Keep `.env` and all real secrets private.
- Enforce authorization in the backend; hiding UI elements is not sufficient.
- Treat retrieved document text as untrusted input.
- Re-check current permissions before passing chunks to the LLM.
- Review denial messages to ensure they do not disclose sensitive document metadata.
- Run security and leakage tests separately from RAGAS quality evaluation.

## Project status and limitations

The documented workflows and metrics reflect the project and saved v2 evaluation. Confirm exact routes, database schema, supported document formats, active model configuration, and deployment readiness in the current repository and environment. Evaluation scores alone do not establish production readiness.

## License

This project is licensed under the [MIT License](./LICENSE).
