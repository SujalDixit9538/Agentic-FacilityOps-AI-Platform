# Agentic FacilityOps AI Platform
## Complete Audit Report

**Audit date:** 2026-09-01  
**Audit mode:** Read-only review plus live runtime probes. This report is the deliverable for the next implementation pass.

## Executive assessment

The project has a usable prototype foundation, but it is **not production-ready** and should not yet be presented as a reliable enterprise platform. The API and Streamlit containers can start, SQLite data persists in the named Docker volume, and the Maintenance/Occupancy pages demonstrate a stronger visual direction than Cost. However, the platform currently has inconsistent facility identity, duplicated data paths, advertised ML paths that are bypassed, unsafe public APIs, no migrations or authentication, expensive synchronous analysis/seeding, incomplete UI data contracts, and insufficient tests.

The most important product problem is not that the UI is visually imperfect. It is that the UI cannot consistently tell a non-technical user whether data is real, stale, unavailable, simulated, or degraded. The next implementation phase should make data provenance and operational state visible while reducing the number of actions and concepts presented to users.

## Runtime snapshot

| Area | Finding | Assessment |
|---|---|---|
| API | `http://localhost:8000/api/v1/health` returned HTTP 200 and database operational | Works in current container |
| Frontend | `http://localhost:8501/` returned HTTP 200 | Works in current container |
| Docker build | Builds after excluding `.venv` | Works, but image is rebuilt from one combined environment |
| Docker persistence | Named volume `facilityops-data` is used for `/app/data` | Data survives ordinary `down`/`up`; `down -v` deletes it |
| Startup seeding | Disabled in Compose, but local default is enabled | Correct for speed in Compose, inconsistent locally |
| Cost data | `FAC-001` had 18 records after manual seed | Cost page can show data only after deliberate seed |
| Occupancy data | Existing records use `F-0000`-style IDs | Does not correlate with `FAC-001` Energy/Cost |
| Automated tests | Focused cost tests previously passed; full collection fails at occupancy | Quality gate is red |
| Dependency environment | `.venv` has no pytest and versions differ from requirements | Environment is not reproducible |

## Severity model

- **P0:** Security, data loss, or fundamental trust failure. Block production.
- **P1:** Major runtime, correctness, or core workflow failure. Fix before user acceptance.
- **P2:** Significant maintainability, performance, UX, or coverage weakness. Fix before production hardening.
- **P3:** Cleanup, polish, or optional improvement.

## P0 and P1 findings

### P0: APIs are unauthenticated and unrestricted

All domain reads, writes, seed operations, analysis calls, manual predictions, work-order generation, and recommendation updates are exposed without authentication or authorization. A caller can trigger expensive operations, mutate recommendations, and read or write facility data.

Evidence: `backend/api/`, especially `backend/api/cost.py`, `backend/api/maintenance.py`, and `backend/api/occupancy.py`.

**Required action:** Add authentication, role-based authorization, facility-level access checks, request size/limit validation, rate limiting, and audit logging. Treat seed/demo endpoints as development-only or protect them behind an explicit admin role.

### P0: CORS is unsafe for production

`backend/main.py` configures `allow_origins=["*"]` together with `allow_credentials=True`.

**Required action:** Use an environment-configured explicit origin allowlist. Disable credentials unless they are required by the selected authentication mechanism.

### P0: Facility identity is not a shared contract

Energy and Cost use `FAC-001`/`FAC-002`; Maintenance and Occupancy seed `F-0000`-style IDs from `data/processed_facilities.csv`. The executive report therefore frequently combines unrelated or missing domain data. The current live API demonstrated this directly: Cost facilities returned `FAC-001`, while Occupancy returned `F-0000` through `F-0010`.

Evidence: `backend/main.py`, `frontend/pages/Energy.py`, `frontend/pages/Cost.py`, `frontend/pages/Dashboard.py`, `backend/services/mock_*.py`.

**Required action:** Create one `facilities` table/catalog and one canonical ID format. Every domain, seed path, UI selector, report, and permission check must use it. Migrate existing records rather than silently joining different IDs.

### P0: Database changes have no migration system

`Base.metadata.create_all(bind=engine)` runs during import in `backend/main.py`. It creates missing tables but does not safely upgrade existing schemas, detect drift, or support rollback.

**Required action:** Add Alembic migrations, a migration check in readiness, backup-before-upgrade documentation, and a controlled deployment command. Do not use `create_all()` as the production schema-management mechanism.

### P1: Health/readiness semantics are misleading

`backend/api/health.py` can return top-level `status: healthy` and HTTP 200 while the database status is `degraded`. Compose uses this endpoint for readiness. Startup seeding also catches broad exceptions and continues, allowing a partially seeded application to appear ready.

**Required action:** Separate liveness from readiness. Readiness should verify database connectivity, required tables/migrations, model artifact availability, and optional data-plane status. Return a non-healthy status and appropriate HTTP status when required dependencies are unavailable. Keep demo seeding out of readiness.

### P1: Cost analysis has side effects on a GET and is not idempotent

`GET /cost/analyze/{facility_id}` persists a new report and recommendations every time it runs. The Cost page calls it during every page render. Refreshing the page can create duplicate reports and recommendations.

**Required action:** Make analysis an explicit `POST` command or add a stable run key and deduplication policy. Keep `GET` for retrieving the latest persisted result. Define report retention and recommendation uniqueness rules.

### P1: EnergyAgent bypasses its real ML implementation

`backend/agents/energy/agent.py` currently performs a separate threshold calculation and does not invoke `EnergyAnalyzer`, `EnergyActionEngine`, or the energy model artifacts. The live threshold is `peak_kw > 200`, while Energy configuration defines a 75 kW threshold. This makes the advertised Energy ML/rules behavior misleading.

**Required action:** Select one supported Energy pipeline, wire the real analyzer into the agent, use configuration thresholds, add exact feature-frame tests, and expose model/rules provenance in the response.

### P1: Maintenance fallback invents telemetry

`backend/agents/maintenance/analyzer.py` substitutes fixed values for missing sensor inputs. Its fallback checks a `temperature` field while production records use `air_temp` and `process_temp`. A prediction can therefore look valid while being based on fabricated values, and the intended temperature rule may never fire.

**Required action:** Define required and optional features. Reject incomplete ML input or return an explicit degraded result. Align fallback rules to the actual schema and include missing-feature metadata in the API.

### P1: Occupancy data isolation has a cross-facility query risk

`backend/repositories/occupancy_repository.py:get_latest_occupancy_by_zone()` filters its subquery by facility but joins the outer query using only `zone_id` and timestamp. Reused zone IDs can return another facility’s record.

**Required action:** Include `facility_id` in the join and add a cross-facility regression test.

### P1: FacilityStateService calculates occupancy from one record

`backend/services/facility_state_service.py` selects one latest occupancy record for the whole facility and divides it by total capacity. Occupancy is stored per zone, so this is not a facility utilization calculation.

**Required action:** Select the latest record per zone, aggregate counts, calculate utilization, and return the timestamp/freshness of the aggregate. Add missing-zone and stale-zone behavior.

### P1: Alert identifiers can collide

`backend/services/alert_service.py` creates IDs from the current Unix timestamp in seconds. Multiple alerts emitted in one analysis can share the same ID.

**Required action:** Use UUIDs or deterministic IDs containing facility, source, event identity, and timestamp. Persist alert identity if alert deduplication is required.

### P1: Executive analysis is expensive and serial

`backend/agents/executive/agent.py` analyzes up to 25 assets individually. Each analysis may perform multiple queries and model/LLM work. A single executive request can become dozens of sequential operations and is currently triggered synchronously.

**Required action:** Batch repository queries, compute fleet-level maintenance features once, cap work explicitly, use bounded concurrency only where safe, add timeouts, cache short-lived results, and expose per-agent latency/status.

### P1: Executive health score is not yet trustworthy

The score averages asset health, occupancy percentage, and optional energy efficiency. It does not include security risk, cost health, data freshness, or documented weights. Missing inputs change the denominator and can make the score incomparable between facilities.

**Required action:** Document the scoring formula and version it. Include all required domains, freshness/data-quality penalties, component scores, and an `unknown` state when the score cannot be responsibly calculated.

## P2 findings: data, ML, and agent behavior

### Cost intelligence

- Cost records do not validate category vocabulary, non-negative amount, facility existence, date bounds, or query limits. Evidence: `backend/schemas/cost.py` and `backend/api/cost.py`.
- Cost model predictions are not checked for finite values, negative savings, output labels outside the supported action map, or model version compatibility.
- Empty cost analysis places `intelligence_source` at a different response level than non-empty analysis; persisted report metadata reads only the nested path and can record `Unknown`.
- Persisted recommendations discard rationale, assumptions, owner, time horizon, success metric, model version, and degradation metadata.
- Report history returns only summary metadata, so the promised audit/export workflow is incomplete.
- The cost seed service is random, commits each row individually, and is explicitly demo data. It should be deterministic for tests and clearly labeled in the UI.

### Energy intelligence

- `EnergyRecord` has no temperature field, while Energy ML expects temperature-like context; the analyzer uses a constant fallback.
- Nullable `peak_demand_kw` is not consistently handled by rules/ML code.
- The frontend displays hardcoded or unconditional values such as efficiency, month-over-month change, cost rate, emissions, and budget status in `frontend/pages/Energy.py`.
- The “7-Day Forecast” is not a real forecast presentation; the calculated rolling value is not plotted as a forecast series.
- Energy action buttons provide UI feedback without an API action or persisted outcome.

### Occupancy/security intelligence

- The analyzer, dashboard, and seed behavior use different overcrowding thresholds.
- The occupancy seed function resets the requested `days` value to 30, so callers cannot control the requested period.
- Occupancy seeding commits individual rows and creates thousands of rows per facility, causing the multi-minute startup observed in the container logs.
- Occupancy history sums hourly readings rather than selecting an average/latest/peak policy, so daily utilization can be inflated.
- Missing occupancy is represented as zero, indistinguishable from a truly empty zone.
- Security has no LLM reasoning layer despite the project decision log describing ML signal followed by reasoning as the agent standard.
- `tests/test_occupancy_analyzer.py` is currently not a reliable regression test; collection fails because it calls a missing `_load_models()` method.

### Maintenance intelligence

- Maintenance logs are not directly facility-scoped and rely on asset lookup without a complete ownership contract.
- Logs missing `air_temp` are dropped even if other useful features exist.
- Manual prediction failures are exposed as generic server errors rather than controlled degraded responses.
- The Maintenance page performs an N+1 asset analysis workflow and should use a fleet endpoint.

### Cross-agent orchestration

- Maintenance was previously instantiated but omitted from executive polling; the current patch adds it, but the approach remains serial and expensive.
- The executive LLM prompt historically names Energy, Occupancy, and Cost while maintenance data is present in the payload. Prompt/schema/version alignment is required.
- Cross-agent state has no shared `as_of` contract, freshness budget, error policy, or correlation ID.
- LLM availability/model errors are logged, but the response does not consistently expose whether reasoning was generated, degraded, or unavailable.

## P2 findings: UI and user experience

The target audience is non-technical facility operators. The current pages still make them interpret raw agent language, know which seed button to press, and distinguish empty data from an outage.

### Cost page

- The page previously consisted mostly of explanatory text, a seed button, a data table, and a manual analysis button. It now renders analysis automatically, but it still needs a proper operator-oriented layout.
- Replace the current flow with: facility header/status, spend KPI row, cost trend, category breakdown, budget variance, top recommendations, savings estimate, confidence/provenance, and recommendation status controls.
- Use compact cards only for repeated metrics. Avoid exposing raw model terminology as the primary experience; show “Data quality” and “Recommendation confidence” with expandable technical detail.
- Do not show `$0`, `N/A`, or empty cards as if they were real values. Show “No data received” or “Awaiting telemetry” with a clear next action.

### Energy page

- The missing `streamlit-autorefresh` dependency was fixed and pinned to the available `1.0.1`, but dependency changes must be rebuilt into the image.
- Facility selectors and displayed facility identity are inconsistent and partly hardcoded.
- Hardcoded metrics make the page look complete while being untrustworthy. All displayed metrics need API provenance.
- Replace action buttons that do nothing with either working API calls or remove them.

### Occupancy page

- The page now discovers actual occupancy facilities, but its fallback still lists incompatible `FAC-*` IDs.
- The file contains large commented-out historical implementations and duplicated UI paths, increasing the chance of rendering the wrong section.
- The page makes several sequential API calls on every rerun, including up to 8,000 records; add a dashboard endpoint with one response and cache by facility/time window.
- Distinguish “API unavailable,” “no zones,” “no recent telemetry,” and “zero occupants.”

### Executive dashboard

- Facility selection is still hardcoded and incompatible with the canonical facility issue.
- The page only produces the main report after a button click and has no report history or last-updated state.
- Add visible health-score components, freshness, domain status, active alert count, recommendation queue, cost/resource/sustainability metrics, and agent performance.

### Shared frontend quality

- `frontend/services/api_client.py` has fixed timeouts and generic fallbacks but no retry/backoff, correlation ID, response schema validation, or stale-cache policy.
- `frontend/components/ui.py` interpolates some values into HTML without consistent escaping. Treat database and LLM content as untrusted.
- Streamlit emits repeated `use_container_width` deprecation warnings; migrate to `width` before the dependency removes the old option.
- External Google Fonts create an unnecessary network dependency for a facility operations console; bundle or use a local font policy if offline/enterprise deployment matters.
- Add page-level smoke tests or a browser test for operational, empty, degraded, and failure states.

## P2 findings: performance and persistence

### Startup and seeding

- First startup previously took several minutes because occupancy seeding generated approximately 8,000 records per facility and committed each row individually.
- Seed functions generally perform one transaction per record. Replace with bulk insert and one transaction per facility/dataset.
- Seeders should be explicit commands, not application startup work. Keep `AUTO_SEED_DEMO_DATA=false` for production and provide a documented demo profile.
- Use deterministic fixtures for tests and a small demo dataset for UI previews.

### Database

- SQLite is acceptable for local/demo mode, but not a safe default for concurrent enterprise API/UI writes. It has no backup, migration, lock monitoring, or retention strategy.
- Recommended deployment tiers: SQLite for local development only; PostgreSQL for shared/staging/production.
- Add indexes for facility plus timestamp on all time-series tables, unique constraints for idempotency keys, foreign keys, and data retention policies.
- Make transactions explicit for mirrored writes such as occupancy image plus occupancy record.

### Caching and API shape

- `backend/services/cache_service.py` appears unused; either wire it into short-lived report/telemetry caching or remove it.
- Prefer aggregate dashboard endpoints over pages fetching raw records and recomputing metrics in Streamlit.
- Cache model loading at process scope and avoid reloading artifacts for each asset/request.
- Add request timing, query timing, model timing, and LLM timing metrics before optimizing blindly.

## P2 findings: dependency and environment audit

### Why `.venv` is approximately 1 GB

The current `.venv` is approximately **975 MB**. The largest installed packages measured were approximately:

| Package area | Approximate size | Notes |
|---|---:|---|
| `pyarrow` | 153 MB | Streamlit/transitive data stack; verify whether required by the UI |
| `scipy` | 111 MB | Scikit-learn dependency; likely required by current ML artifacts |
| `googleapiclient` | 100 MB | Not declared in `requirements.txt` and no runtime Google API imports found |
| `pandas` | 73 MB | Used heavily by agents/UI/seeding |
| `plotly` | 68 MB | Used by dashboards |
| `scikit-learn` | 57 MB | Required by current model artifacts |
| `numpy` | 43 MB | Required by pandas/scikit-learn/models |
| `google` packages | 36 MB+ | No active Google/Gemini runtime usage found; likely historical environment residue |
| Streamlit | 35 MB | Required by current frontend |

There is also approximately **430 MB** in the user pip download cache, separate from `.venv`.

The size is not caused by the project source. It is mainly native scientific libraries and packages left from broader historical dependencies. A clean environment created from the current requirements should be smaller, but the current requirements themselves are not reproducible because the active environment differs materially:

- Declared `pydantic==2.6.3`; installed `2.13.4`.
- Declared `uvicorn==0.27.1`; installed `0.52.1`, and package metadata lookup did not match the `uvicorn[standard]` requirement.
- Declared `requests==2.31.0`; installed `2.34.2`.
- Declared `streamlit>=1.37.0`; installed `1.60.0`.
- Current `.venv` does not contain pytest even though tests import it.

**Recommendation:** Maintain separate dependency files:

- `requirements-api.txt`: FastAPI, SQLAlchemy, pandas/numpy/scikit-learn/joblib, Groq, config/logging.
- `requirements-frontend.txt`: Streamlit, Plotly, requests, autorefresh.
- `requirements-dev.txt`: pytest, coverage, ruff, mypy/pyright, HTTP/browser test tooling.

Recreate environments from lock files rather than deleting packages manually. Do not commit `.venv`. Remove unused historical Google/Gemini packages after confirming no active import or deployment requirement. Keep scipy/numpy/scikit-learn unless the models are retrained with a lighter inference stack.

## P2 findings: repository hygiene and maintainability

- `.gitignore` ignores `.env.example` and `tests/*`; this is backwards for a project that needs a shareable configuration example and tracked tests. Fix the ignore rules and explicitly ignore only generated test artifacts.
- The current worktree contains substantial uncommitted changes, including prior Occupancy changes and new deployment/cost changes. Establish a clean baseline or commit in reviewable slices before further implementation.
- `diff.patch` is untracked and should either be removed, named/documented, or moved into a deliberate patch archive.
- `backend/agents/energy/analyzer.py` and `backend/agents/executive/agent.py` contain large commented-out implementations. Preserve history in Git, then remove dead blocks.
- `backend/models/` and `backend/prediction/` are scaffolding-only packages. Keep only if there is a dated implementation milestone; otherwise remove.
- `backend/agents/energy/predictor.py`, `backend/agents/energy/tests.py`, `backend/services/cache_service.py`, and several frontend helpers appear unused. Confirm with import analysis before removal.
- `data/live_iot_stream.py` is a second ingestion implementation with hardcoded facility/price and a direct SQLite write path. Consolidate it into the repository/schema path or remove it.
- `backend/database/models/maintenance.py` has duplicate column and relationship declarations. Remove duplicates and add a schema migration if the effective schema changes.
- `backend/schemas/maintenance.py` declares `MaintenanceLogResponse` twice.
- Settings are not fully centralized: agents call `load_dotenv()`/`os.getenv()` independently and model names/timeouts are duplicated.
- `frontend/pages/Settings.py` is a placeholder and should either expose real safe operational configuration or be removed from navigation.
- `README.md` is currently a quick-start document, not a system/operator/deployment guide. Expand it after behavior stabilizes.

## Test and quality-gate assessment

Current test coverage is insufficient for the requested “no discrepancies” standard.

Observed:

- Focused cost regression tests previously passed (`3 passed`).
- Full collection fails before running all tests because `tests/test_occupancy_analyzer.py` calls missing `OccupancyAnalyzer._load_models()`.
- `.venv/bin/pytest` does not exist; the test runner is only available outside the declared environment.
- IDE diagnostics and Python compilation passed for the recently touched modules, but that is not a substitute for integration coverage.

Required test layers:

1. **Unit:** feature construction, thresholds, model artifact compatibility, finite prediction validation, fallback/degradation, action mapping, scoring formula.
2. **Repository:** facility isolation, latest-per-zone queries, indexes, transaction rollback, idempotency.
3. **API:** schema validation, authorization, status codes, pagination/limits, readiness, report history/export, recommendation lifecycle.
4. **Agent:** Energy, Cost, Occupancy/Security, Maintenance, and Executive orchestration with mocked ML/LLM dependencies.
5. **Frontend/browser:** every page in operational, empty, stale, degraded, and API-failure states.
6. **Deployment:** clean environment installation, migration, Compose startup, health/readiness, restart persistence, backup/restore.
7. **Performance:** cold startup, warm startup, cost analysis latency, executive report latency, query counts, seed throughput.

## Keep / fix / remove decisions

### Keep

- FastAPI + service/repository separation.
- SQLAlchemy domain models, after migrations and constraints are added.
- Existing ML artifacts only where feature contracts can be verified.
- Maintenance’s structured work-order pattern as a reference for agent output.
- Occupancy zone generator and spatial dashboard direction, after facility identity is centralized.
- Plotly and Streamlit for the current lightweight internal-console target.
- Docker for reproducible packaging, but not as a reason to use SQLite in enterprise production.

### Fix

- Facility catalog and all cross-domain joins.
- Authentication, authorization, CORS, rate limits, and audit logging.
- Migrations, readiness, backup, and database selection.
- Energy real analyzer wiring and all hardcoded UI metrics.
- Cost analysis idempotency and report/recommendation provenance.
- Occupancy latest-per-zone and threshold consistency.
- Maintenance missing-feature behavior.
- Executive batch orchestration and health-score contract.
- UI data states, Cost information architecture, and frontend API caching.

### Remove or consolidate after confirmation

- Historical commented-out implementations.
- Unused Google/Gemini dependency residue and configuration if no active integration is approved.
- Direct SQLite live stream duplicate.
- Unused predictor/cache/scaffolding modules.
- Duplicate model/schema declarations.
- Buttons that have no backend action.
- Hardcoded metrics and incompatible fallback facility lists.

## Recommended target architecture

### Local/demo

- One command starts API and Streamlit.
- SQLite persisted in a local data directory or Docker volume.
- Small deterministic demo fixture loaded through an explicit command.
- Groq optional; rules and local ML always produce structured output.
- No authentication only when bound to localhost and clearly labeled development mode.

### Shared/staging/production

- FastAPI API container, Streamlit UI container, PostgreSQL database, and a one-shot migration job.
- Authentication/authorization and explicit CORS allowlist.
- Background worker for analysis/report generation if latency exceeds the interactive budget.
- Redis or equivalent only when measured cache/queue requirements justify it.
- Model artifacts versioned with checksums and feature contracts.
- Structured logs, metrics, traces, request correlation IDs, backups, restore drills, and alerting.

## Proposed implementation backlog

### Phase 0: Stabilize the baseline

1. Preserve or commit current user changes in reviewable slices.
2. Fix `.gitignore`, create clean API/frontend/dev requirements, lock versions, and install pytest.
3. Make all pages import and render without exceptions.
4. Fix test collection and establish a green baseline.

### Phase 1: Data trust

1. Add canonical facilities catalog and migrate IDs.
2. Add Alembic migrations, constraints, indexes, and transaction boundaries.
3. Correct latest-per-zone occupancy and shared facility-state aggregation.
4. Add provenance/freshness/degraded fields to every domain response.

### Phase 2: Agent correctness

1. Wire EnergyAgent to EnergyAnalyzer and remove hardcoded metrics.
2. Make Cost analysis command/retrieval idempotent and fully auditable.
3. Remove invented Maintenance telemetry and validate model outputs.
4. Align Occupancy/Security thresholds, anomaly deduplication, and security reasoning.
5. Define and test Executive orchestration, health score, and failure policy.

### Phase 3: Fast operation

1. Batch all seed inserts and move seeding to explicit commands.
2. Add aggregate dashboard endpoints and short-lived caching.
3. Batch fleet analysis and eliminate N+1 queries.
4. Add latency/query/model/LLM telemetry and set response budgets.

### Phase 4: Usable product UI

1. Redesign Cost around operator decisions rather than agent narration.
2. Make Dashboard the default facility overview with health, alerts, recommendations, utilization, cost, and sustainability.
3. Replace hardcoded selectors with the facilities catalog everywhere.
4. Implement or remove every action button.
5. Add clear empty/stale/offline/degraded states and browser smoke tests.

### Phase 5: Production hardening

1. Add auth/RBAC, CORS, rate limits, secrets policy, and audit logs.
2. Move shared deployment to PostgreSQL with backups and restore testing.
3. Add CI for formatting, lint, type checks, tests, image build, vulnerability scan, and migration check.
4. Publish an operator runbook and release checklist.

## Acceptance criteria for the next implementation pass

- A new clean environment installs exactly the declared locked dependencies and runs tests.
- A normal restart does not reseed or duplicate data and completes readiness quickly.
- One canonical facility ID produces correlated Energy, Cost, Occupancy/Security, and Maintenance data.
- No UI metric is hardcoded or presented as real when unavailable.
- Every ML/LLM/rules response states source, model version, freshness, and degradation reason.
- Cost analysis does not duplicate reports on refresh.
- Executive analysis completes within a measured response budget and reports per-agent status/latency.
- Database failure, stale telemetry, missing model, LLM failure, and empty facility states are all visible and actionable.
- Unauthorized requests cannot read or mutate facility data.
- The Cost page is understandable without knowing what an “agent” or model fallback is.

## Suggested first implementation request

“Implement Phase 0 and Phase 1 from `PROJECT_AUDIT_REPORT.md`: clean the dependency/test baseline, centralize facility IDs, add migrations and constraints, fix readiness semantics, and make every page render with explicit empty/degraded states. Do not add new features until the baseline test suite is green.”