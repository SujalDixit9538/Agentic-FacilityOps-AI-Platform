# Agentic FacilityOps AI Platform

## Production quick start

1. Copy `.env.example` to `.env` and configure `DATABASE_URL`, `API_AUTH_TOKEN`, `API_ADMIN_TOKEN`, `CORS_ORIGINS`, and the grid emissions factor. Use long, unique secret values for both API tokens.
2. Start the API and Streamlit executive console:

	`docker compose up --build -d`

3. Open `http://localhost:8000/api/docs` or `http://localhost:8501`.

The API applies database migrations before startup. Keep the database volume backed up before deploying migration changes. `/api/v1/health` is public for liveness checks; domain routes require `Authorization: Bearer <API_AUTH_TOKEN>`, and state-changing requests require `API_ADMIN_TOKEN`.

Demo data is never seeded during API startup. Run `python scripts/seed_demo.py` explicitly for a local demo dataset, or use the module seed endpoints. Aggregate dashboard responses target 2 seconds and analysis responses target 10 seconds; request timing is returned in the `X-Process-Time` header. Cost analysis uses the persisted ledger plus current energy, occupancy, and asset state. If a required signal is missing, the API reports explicit degraded intelligence instead of substituting constants. Reports and recommendation outcomes are stored for audit.