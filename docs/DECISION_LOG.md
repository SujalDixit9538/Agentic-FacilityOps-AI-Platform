# Agentic FacilityOps AI Platform — Decision Log

Living record of architectural decisions, standing rules, and forward specs.
Lives in the repo (not GitHub Issues/Wiki) so it survives Codespace resets and
carries context across Claude sessions. Update this file whenever a decision
is made that a future session (Claude, Gemini, or Employee AI) would need to
know without re-deriving it. Newest entries at the top of each section.

---

## Standing Rules (do not violate)

1. **Commit AND push immediately after every change.** Not just commit — a
   commit that sits in Codespace and never reaches `origin` does not exist for
   audit purposes. (Milestone 1 lost work to this; the Maintenance hotfix
   push-gap and a likely Occupancy/Security split are the two confirmed
   repeat instances — see Known Issues.)
2. **Audit the live repo before trusting a status report.** Pull `origin`,
   check commit hashes, inspect actual DB state. Reported "done" has been
   wrong before (nested-metrics bug, hardcoded fallback constants, dead code
   masquerading as live).
3. **ML models provide structured signal; Groq provides reasoning — never the
   reverse.** A heuristic formula standing in for either is not agentic
   behavior. Pattern per agent: `ML model → structured metrics → Groq LLM →
   decision/justification/generated text`.
4. **Gemini output is reviewed by Claude before it hits the repo.** Catches
   import path mismatches, naming collisions, and copy-paste fallback
   constants before they're load-bearing.
5. **UI stays lightweight** — Streamlit + custom CSS + Plotly only. No React
   or heavier frameworks.
6. **Fill the UI, don't leave empty space.** Empty dashboard real estate reads
   as unfinished/poor design. When building or reviewing a page: prefer dense
   layouts — multi-column metric rows, secondary charts, recent-activity
   feeds, or supporting detail panels — over a couple of centered widgets on
   an otherwise blank page. Applies to all remaining UI work (Energy rebuild,
   Occupancy/Security, Cost, Executive/Dashboard).

---

## Why "agentic" hasn't actually been true yet (established this session)

Ingestion + ML scoring + a dashboard + CRUD endpoints is a **monitoring app**,
not an agent platform, regardless of what the folders are named. Per the
project brief's own framing, "agent" means something reasons and decides —
not just scores and displays.

Concrete definition adopted for this project: an agent takes ML-model output
(health_score, failure_probability, predicted_issue, raw telemetry) and uses
an LLM (Groq) to reason over it — deciding urgency, drafting real work-order
text, deciding whether to escalate, cross-referencing multiple assets to
prioritize a fleet-wide action list. Maintenance's `generate_work_order` is
the first real instance of this and is the template every other agent should
converge on. Energy and Cost currently fail this test in different ways (see
Known Issues) — Energy skips the ML step entirely, Cost's ML step silently
falls back to constants.

---

## Chatbot v1 — spec (deferred, execution-phase separate from this)

Stronger agentic story than a static work-order generator: right now the
agent only reasons about assets already identified in the DB by ID. A
free-text query forces genuinely new capability — parsing an unstructured
symptom report, mapping it to a real asset (or asking which one), and
reasoning without a clean ML feature vector handed to it up front.

**v1 scope — query only, no state mutation:**
Free-text input → LLM extracts intent (asset/location hint, symptom,
severity) → cross-reference against real asset data if a match is found
(health_score, failure_probability, recent logs) → LLM responds with a
synthesized answer + recommended urgency, same reasoning style as
`generate_work_order` but conversational.

**v2 — execute/deploy option (later phase, explicitly gated):**
Chatbot proposes an action ("create a Critical work order for AST-XXXX") →
user approves → only then does it call the real `generate_work_order` /
status-mutating logic. Kept as a distinct, reviewable phase — no silent LLM
state mutation, per Standing Rule 3's spirit extended to the chatbot.

Sequencing: current milestone work (Energy/Cost fixes, Executive wiring,
Occupancy/Security) finishes first. Chatbot is the next major feature after
that, v1 before v2, always.

---

## Known Issues / Backlog (live — check off as fixed, don't delete history)

### Cleanup landed outside a planned chunk (commit `fb82ce3`, message ".")
- [x] `Energy.py` — ~267 lines of dead commented-out code removed. Live code
      (the still-fake `analyze_facility`) untouched — Chunk 1 Energy fixes
      still apply as scoped.
- [x] `Maintenance.py` — seed-response handler now tolerates both list and
      dict API responses for `assets_seeded`.
- [ ] NOT fixed by this commit, still open: `st_autorefresh` unconditional
      import crash (Chunk 1) — code untouched, still crashes on clean
      install.
- [ ] `data/facilityops.db` was re-committed in this same commit (2nd
      regression of the untrack issue, see Chunk 3). Whatever runs `git add
      .` before commits needs to actually respect `.gitignore`, not rely on
      periodic manual `git rm --cached`.

### Confirmed broken, fix in progress (Chunk 1 — Energy + Cost)
- [ ] `EnergyAgent.analyze_facility()` returns hardcoded `total_kwh: 4500,
      peak_kw: 210` for every facility. Real 368-line hybrid ML/rules
      analyzer already exists and works (verified: feature vector matches
      `energy_model_total_v1.joblib` exactly) — needs `agent.py` rewired to
      call it instead of the stub, not rebuilt from scratch.
- [ ] `frontend/pages/Energy.py` imports `streamlit_autorefresh`
      unconditionally at module load; package is commented out of
      `requirements.txt`. Crashes the page on any clean install. Trivial fix
      — either install it for real or make the import conditional.
- [ ] `EnergyRecord` DB model has no temperature column; mock energy seeding
      is pure random noise unrelated to any real dataset. Even after the
      agent rewire, ML predictions will barely vary per facility because the
      temperature feature always falls back to a constant (22.5). Real fix
      needs either a temperature field wired into seeding, or migrating to
      `data/processed_energy_daily.csv` (503,867 real rows, real `F-XXXX`
      IDs, currently referenced nowhere in the codebase).
- [ ] `CostAnalyzer`'s prescriptive ML path pulls `energy_load`,
      `asset_health`, `occupancy_pct` from `cost_records[-1]`, which never
      contains those fields (cost records only have category/amount/
      description/incurred_date). Silently falls back to hardcoded constants
      (310.0 / 55.0 / 15.0) every single call — same bug family as the
      Maintenance nested-metrics bug, just less visible because the
      surrounding code is otherwise real. Needs a real cross-agent state feed
      (e.g. Executive/orchestrator passes live energy load, avg asset health,
      current occupancy into the Cost call).
- [ ] `ExecutiveAgent.generate_executive_summary()` reads
      `energy_report["analysis"]["metrics"]["efficiency_score"]` — key does
      not exist in either the fake or real energy metrics payload. Always
      renders "N/A". Cosmetic but bundle into whichever pass touches
      Executive next.

### Confirmed broken, audited (Chunk 2 — Occupancy & Security + Executive) — CLOSED, fixes not yet applied
- [ ] `ExecutiveAgent.generate_executive_summary()` instantiates `MaintenanceAgent`
      (agent.py line 114) but never calls it (poll section is lines 139-141,
      maintenance absent). One-line-scope fix, highest-impact for next demo.
- [x] Confirmed the earlier `Security.py` split was cosmetic only — all
      security logic already lived in the combined file. Decision made: keep
      integrated, empty `Security.py` stub removed. File is
      `Occupancy_and_Security.py`.
- [ ] Occupancy half of `OccupancyAnalyzer` is genuinely solid — real
      regression model, correct feature schema, believable seeded data. No
      action needed.
- [ ] Security half is silently non-functional: Isolation Forest needs
      `zone_level`/`recent_failed_attempts`, analyzer derives both via
      keyword-matching on `event_type`, but the mock seeder's four event
      types (`Unauthorized Access`, `Door Left Open`, `Tailgating Detected`,
      `After-hours Motion`) never match any of the checked keywords
      (`server`/`restricted`/`office`/`failed`/`denied`). Every event gets
      zone_level=0, failed_attempts=0, always — dead ML path, differentiated
      only by hour/day. `SecurityEvent` DB model has no zone or
      failed-attempts field at all, so this isn't a wiring gap like Cost —
      the schema itself never captured what the model needs. Rules-fallback
      (open+high/medium severity) still fires independently, so real alerts
      aren't lost, ML layer just adds nothing. Needs either new DB
      columns+real seeding, or dropping the ML claim and being honest it's
      rules-based for security specifically.
- [ ] No Groq/LLM call anywhere in Occupancy/Security agent — pure ML+lookup
      table. Doesn't meet the project's own agentic bar yet (see philosophy
      section above), unlike Maintenance.
- [ ] `Occupancy_and_Security.py` frontend still hardcodes
      `["FAC-001","FAC-002"]` facility selectors in two places — same root
      cause as everywhere else, fix centrally (Chunk 3 facility-ID item).
- [x] Occupancy model v2 + analyzer.py capacity-tier patch — FULLY CLOSED,
      verified end-to-end via Employee AI. Fixed zone taxonomy mismatch
      between Colab training (transit-hub metaphor) and production
      (keyword-matching). v2 derives zone_type from real room capacity via
      3 tiers (>=100 cap = 0, 20-99 = 1, <20 = 2) instead of name keywords.
      analyzer.py's get_zone_type() patched to use capacity-tier lookup via
      self.capacities (already existed, no new dependency).
      Verification (mocked clock, Tue 9AM): intelligence_source = "ML
      (Partial/Dual Pipeline)", zero false anomalies at normal load
      (Cafeteria 160/200, Main Lobby 130/150), correctly flags genuine
      near-capacity (195-198/200). Live API endpoint confirmed same
      behavior. One false alarm during testing (Cafeteria/Lobby flagged
      identically at baseline 61.3) was traced to the test script using
      live server wall-clock time instead of the mocked timestamp — not a
      code bug, root-caused and reproduced correctly on retest.
      Known residual limitation, acceptable at current scale: rooms sharing
      a tier (Main Lobby 150 vs Cafeteria 200, both tier 0) get identical
      baseline predictions — would need a continuous capacity feature if
      more varied-capacity rooms get added later.
      Note for later: analyzer uses live datetime.utcnow() for time-context,
      not the occupancy record's own timestamp — fine for live monitoring,
      but a future "historical replay" feature would need an explicit
      as_of parameter threaded through instead.
- [ ] Security and Cost models still need the same "shared generator between
      training and production" treatment discussed above — not yet started.

### Structural, cross-cutting (Chunk 3 — polish + shared code)
- [ ] `data/facilityops.db` is tracked in git *again* despite being
      "untracked" in commit `1a39ce2` — the very next Maintenance commit
      (`bc5d334`) re-added it as a binary diff even with `data/*.db` already
      in `.gitignore`. Needs `git rm --cached data/facilityops.db` plus
      whatever is doing `git add .`/force-adds in the commit workflow needs
      to stop scooping it back up.
- [ ] Facility ID fragmentation: Maintenance seeds from the real 1,449-row
      `processed_facilities.csv` (first 15 only, `F-XXXX`). Energy,
      Occupancy/Security, and Cost are all hardcoded to `FAC-001`/`FAC-002`
      in `backend/main.py`'s startup seeding, with no shared source of truth.
      This is the root cause of the modules feeling disconnected from each
      other and should be fixed once, centrally, rather than per-agent.
- [ ] Dead code, confirmed via `vulture` + manual cross-reference, safe to
      remove: `backend/agents/energy/predictor.py`,
      `backend/agents/energy/tests.py`, `backend/services/cache_service.py`,
      `frontend/components/{filters,layout,charts}.py`,
      `config/{feature_flags,constants,thresholds}.py`. Also
      `data/live_iot_stream.py` — orphaned, purpose unconfirmed, check before
      removing.
- [ ] Empty scaffolding folders `backend/models/`, `backend/prediction/` —
      nothing but empty `__init__.py`.
- [ ] Design system split — Maintenance uses the new dark theme
      (`theme.py`/`ui.py`); Energy and Occupancy/Security still use the older
      component set. Gemini-generated unification code was reviewed but not
      committed; two flagged issues: unresolved import path
      (`from theme import COLORS`) and possible naming collision with
      existing `frontend/components/{kpi_cards,charts,layout,status}.py`.

### Resolved (kept for history, don't re-investigate)
- [x] `generate_work_order` nested-metrics bug (health_score/
      failure_probability read at wrong dict level, defaulted to 100/0) —
      fixed in `fd329fa`.
- [x] Telemetry-poisoning bug in ML input for stub work orders — fixed in
      `2060349`.
- [x] Maintenance hotfix push-gap (committed in Codespace, never reached
      `origin`) — confirmed resolved, commit history now matches reported
      state as of this audit.
- [x] `data/facilityops.db` untracked + `.gitignore` updated in `1a39ce2` —
      **note:** this regressed one commit later, see Chunk 3 backlog above.
      Don't mark this fully resolved until the regression is also fixed.

---

## Architecture / Data Reference

- **Repo**: `github.com/SujalDixit9538/Agentic-FacilityOps-AI-Platform`
- **Real facility dataset**: `data/processed_facilities.csv` — 1,449
  facilities, `F-XXXX` IDs. Only Maintenance uses it, only first 15.
- **Unused real dataset**: `data/processed_energy_daily.csv` — 503,867 rows,
  real `F-XXXX` IDs, daily `electricity_kwh`. Not wired into anything yet.
- **ML models** (`models/`): `maintenance_failure_model_v1.joblib`,
  `maintenance_fault_model_v1.joblib`, `energy_model_total_v1.joblib`,
  `energy_model_hvac_v1.joblib`, `cost_action_model_v1.joblib`,
  `cost_savings_model_v1.joblib`, `occupancy_model_v1.joblib` (retrained v2,
  see Chunk 2 — fixed and verified), `security_model_v1.joblib` (audited,
  confirmed dead ML path — retrain pending, see Chunk 2).
- **Groq pattern** (apply identically to every agent): `from groq import
  Groq`, `try/except HAS_GROQ`, `load_dotenv()`,
  `os.getenv("GROQ_API_KEY")`, JSON mode via
  `response_format={"type": "json_object"}`, rules-based fallback on any
  exception.
- **Roles**: Claude = Lead Architect (specs, prompts, review only, no direct
  repo write access). Sujal = Mediator between Claude and two execution
  resources: Employee AI (repo access via Codespaces, free-tier quota) and
  Gemini Flash Lite (bulk code generation, reviewed by Claude before
  Employee AI implements it).

---

## Changelog of this file

- **2026-08-13**: File created. Populated with full audit history through
  Chunk 1 (Energy + Cost), standing rules, chatbot v1/v2 spec, and the
  agentic-definition discussion.
- **2026-08-13 (later same day)**: Confirmed decision log pushed correctly.
  Verified Occupancy/Security split is cosmetic (Security.py empty, logic
  still in Occupancy.py) — Chunk 2 backlog entry corrected. Logged an
  out-of-band cleanup commit (dead code removal in Energy.py, a Maintenance
  UI fix) and a 2nd `facilityops.db` tracking regression. Chunk 2 not yet
  started.
- **2026-08-13 (evening)**: Occupancy model retrained (v2, capacity-tier
  zones) and analyzer.py patched. Full verification cycle run through
  Employee AI — initial false-flag traced to a test-script clock-mocking
  bug, not the fix; retested and confirmed correct. Occupancy fully closed.
  Chunk 2 remaining open item is Security only (dead ML path, needs DB
  schema change + retrain + seeder rewrite) — not yet started.