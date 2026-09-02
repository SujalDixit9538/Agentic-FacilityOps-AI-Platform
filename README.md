# Agentic FacilityOps AI Platform

## Production quick start

1. Copy `.env.example` to `.env` and configure `DATABASE_URL`, `GROQ_API_KEY`, and the grid emissions factor.
2. Start the API and Streamlit executive console:

	`docker compose up --build -d`

3. Open `http://localhost:8000/api/docs` or `http://localhost:8501`.

Demo data is never seeded during API startup. Run `python scripts/seed_demo.py` explicitly for a local demo dataset, or use the module seed endpoints. Aggregate dashboard responses target 2 seconds and analysis responses target 10 seconds; request timing is returned in the `X-Process-Time` header. Cost analysis uses the persisted ledger plus current energy, occupancy, and asset state. If a required signal is missing, the API reports explicit degraded intelligence instead of substituting constants. Reports and recommendation outcomes are stored for audit.