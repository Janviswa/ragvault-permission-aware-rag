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
Qdrant. The frontend is maintained separately.

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
