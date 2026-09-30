# AI Support Ticket Prioritizer

## Run
```bash
docker compose up --build          # Postgres + FastAPI on :8000
cd frontend && npm install && npm run dev   # React on :5173
```
API docs: http://localhost:8000/docs

## How scoring works (backend/nlp.py)
score (0-100) = category weight + customer plan + negative sentiment
+ urgent keywords + legal/churn risk + waiting-time boost.
P1 >= 70, P2 >= 45, P3 >= 20, else P4. Every ticket stores its `reasons`.

## Improve it
- Replace SEED in nlp.py with your real labelled tickets.
- Swap TF-IDF for a transformer (e.g. sentence-transformers) for better accuracy.
- Add auth, Alembic migrations, and webhooks from Zendesk/Freshdesk/email.
