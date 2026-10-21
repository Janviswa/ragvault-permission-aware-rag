# RAGVault Backend

Permission-aware retrieval-augmented generation API. Authorization is enforced
before retrieved content is passed to the language model.

## Run with Docker Compose

1. Copy `.env.example` to `.env`.
2. Set a strong `JWT_SECRET_KEY`, a strong `POSTGRES_PASSWORD`, and any provider
   API keys needed for the features you use. Keep the password in `DATABASE_URL`
   consistent with `POSTGRES_PASSWORD`.
3. Start the backend and its data services:

   ```powershell
   docker compose up --build -d
   ```

4. Check the API at <http://localhost:8000/health>.

The Compose configuration in this repository runs the backend, PostgreSQL, and
Qdrant. The web UI lives in `frontend/` and is started by the same compose file.

## Tests

```powershell
docker compose exec backend pytest -q tests
```

## Evaluation artifacts

The `evaluation/` directory includes the saved v1/v2 benchmark results,
thresholds, datasets, policy corpus, and corresponding PDF reports. Scores in
the JSON files are the values returned during their recorded evaluations.
RAGAS measures answer and retrieval quality; it does not replace security tests
for authorization, tenant isolation, permission revocation, or data leakage.

The checked-in environment template contains placeholders only. Never commit
`.env` or real API keys.

## Web UI

`docker compose up --build` serves the UI at http://localhost:3000 (API at :8000). Sign in with an account an admin created.

Admins land on `/admin` (Dashboard, Users & Roles, Documents, Access Requests, Timeline, Security, Settings).
Everyone else lands on `/workspace` (Documents, Chats, Requests, Settings). A floating chat bubble opens the assistant in both.

Local development without Docker:

```
cd frontend && cp .env.local.example .env.local && npm install && npm run dev
```

`FRONTEND_URL` in the backend `.env` must match the address the UI is served from (CORS).
`NEXT_PUBLIC_COMPANY_NAME` (optional) is shown on the sign-in screen; after sign-in the company name comes from the tenant.

### Backend endpoints added for the UI

| Endpoint | Purpose |
| --- | --- |
| `POST /rag/query` now takes `chat_id`, returns `chat_id` and `restricted` | Saves the conversation; `restricted` is set when the best match is a document the user can't read |
| `GET/DELETE /chats`, `GET /chats/{id}` | Per-user chat history (other users' chats return 404) |
| `GET /me/access-requests` | The caller's own requests, with who can/did decide |
| `GET /admin/analytics/summary` | Dashboard totals and 7-day activity |
| `PATCH /admin/users/{id}` | Change role / activate / deactivate (not your own account) |
| `GET /admin/access-requests?status=` | Now includes requester and document names; filter by status |
| `POST /admin/security/leakage-test` | Probes the retrieval ACL filter as each non-admin user |
| `POST /auth/change-password`, `GET /auth/me` (+`tenant_name`) | Settings page |

New tables (`chats`, `chat_messages`) are created automatically on startup. No existing table changed.

`RESTRICTED_MATCH_MIN_SCORE` (default `0.35`) is the minimum similarity for the "Access restricted" reply. Tune it against your own documents.

Tests for these endpoints (SQLite + in-memory Qdrant, stubbed embeddings/LLM): `pytest -q tests/ui_api`
