## SYNTH MIND REFOCUS PLAN

Based on the [Evaluation Report](EVALUATION_REPORT.md). Three phases: Cut, Fix, Prove.

---

## PHASE 1: CUT (Remove ~4,500 lines of distraction)

Goal: Strip the repo to its thesis. Every file that remains must serve the question: *"Does simulated psychology make an LLM better?"*

### 1.1 Delete Files

| File | Lines | Why |
|------|-------|-----|
| `psychological/collaborative_projects.py` | 600+ | Multi-agent orchestration framework. Zero deployed peers exist. |
| `psychological/federated_learning.py` | 450+ | Privacy-preserving distributed learning. Research-grade scope for an alpha. |
| `psychological/project_templates.py` | 300+ | 10 pre-baked PM templates. GDIL is being simplified, not expanded. |
| `utils/version_control.py` | 200+ | Git auto-commit wrapper. Not the thesis. |
| `utils/ip_firewall.py` | 180+ | Production hardening for zero users. |
| `utils/rate_limiter.py` | 150+ | Same. |
| `utils/access_logger.py` | 120+ | Same. |
| `utils/prometheus_metrics.py` | 100+ | Same. |
| `utils/ssl_utils.py` | 80+ | Same. |
| `utils/harvest_patterns.py` | 100+ | CLI tool for pattern analysis. Defer. |
| `utils/ollama_setup.py` | 60+ | Interactive setup wizard. Nice-to-have, not core. |
| `security/boundary_siem.py` | 300+ | SIEM for a chatbot. Premature. |
| `security/boundary_daemon.py` | 250+ | Trust enforcement. Premature. |
| `security/error_handler.py` | 100+ | Can inline the few needed pieces. |
| `security/__init__.py` | 50+ | Module gone. |
| `PRODUCTION_READINESS.md` | - | No production to be ready for. |
| `KEYWORDS.md` | - | SEO for an unvalidated project. |

**Delete entire directories:**
- `k8s/` - Helm charts, HPA, Ingress, PVC. All premature.
- `monitoring/` - Prometheus + Grafana dashboards for zero traffic.
- `security/` - Entire module is premature.
- `migrations/` - Alembic migrations for a single-user SQLite DB.

### 1.2 Edit Orchestrator (Critical Path)

`core/orchestrator.py` is the integration point. After cuts:

**Remove imports:**
```python
# DELETE these lines:
from psychological.collaborative_projects import CollaborativeProjectManager
from psychological.goal_directed_iteration import GoalDirectedIterationLoop
from psychological.social_companionship import SocialCompanionshipLayer
```

**Remove from `__init__`:**
```python
# DELETE these attributes:
self.social: Optional[SocialCompanionshipLayer] = None
self.gdil: Optional[GoalDirectedIterationLoop] = None
self.collab: Optional[CollaborativeProjectManager] = None
```

**Remove from `initialize()`:**
- Lines 111-135: Social, GDIL, and Collab initialization
- Lines 138-141: Background social task (`_background_social`)

**Remove from `_process_turn()`:**
- Lines 169-187: Entire GDIL active project check block

**Remove from `_handle_command()`:**
- Lines 318-520: All `/project`, `/collab`, `/vcs`, `/template` command handlers (~200 lines)

**Remove methods:**
- `_print_collab_help()` (lines 544-569)
- `_print_vcs_help()` (lines 571-598)
- `_background_social()` (lines 699-704)

**Keep:** `_process_turn()` normal conversation flow (lines 191-252), `_metacognitive_refine()`, `_background_consolidation()` (will be implemented in Phase 2).

### 1.3 Simplify Social Companionship

`psychological/social_companionship.py` has a useful core idea (peer grounding) but is bloated by federated learning. Two options:

**Option A (recommended): Delete entirely.** No peers exist. Re-add when multi-instance deployment is real.

**Option B: Strip to stub.** Remove federated learning import and all `federated_*` methods. Keep `initiate_companionship_cycle()` as a placeholder for future peer interaction.

### 1.4 Simplify GDIL

`psychological/goal_directed_iteration.py` is 1,128 lines. Two options:

**Option A (recommended): Delete entirely.** Multi-turn project tracking is a separate product. The psychological pipeline doesn't need it.

**Option B: Strip to ~200 lines.** Remove template support, VCS integration, multi-project management, archive/pause/switch. Keep: single-project init/plan/iterate/exit cycle. Remove imports of `project_templates` and `version_control`.

### 1.5 Simplify Tools

`core/tools.py` is 843 lines. The sandboxing is excellent code but tool-use is not the thesis.

**Keep:** `calculator`, `code_execute` (showcase the sandbox quality), `json_parse`.
**Remove:** `web_search`, `http_fetch`, `file_read`, `file_write`, `file_list`, `shell_run`, `timer`.

This cuts ~350 lines while keeping the best-engineered parts.

### 1.6 Simplify Dashboard

`dashboard/server.py` imports 5 modules being deleted. Two options:

**Option A (recommended): Simplify to bare WebSocket state viewer.** Remove JWT auth, rate limiting, IP firewall, access logging, SSL, Prometheus. Keep: WebSocket broadcast of internal state + simple HTML dashboard.

**Option B: Delete entirely.** Rebuild when the psychology layer works.

### 1.7 Clean Up Config

`config/personality.yaml` has sections for GDIL, VCS, federated learning, and experimental features that reference deleted modules. Remove those sections. Keep: personality profiles, emotional regulation, predictive dreaming, flow calibration, Mandelbrot weighting, communication style.

### 1.8 Clean Up Tests

- Delete `tests/test_gdil_integration.py`
- Delete `tests/test_dashboard_integration.py` (if dashboard simplified)
- Delete `tests/test_security_e2e.py`
- Remove duplicate mock classes from `tests/test_psychological_modules.py` (use `conftest.py` fixtures instead)
- Keep `tests/test_core_modules.py`, `tests/test_psychological_modules.py`, `tests/test_mandelbrot_e2e.py`

### 1.9 Clean Up Dependencies

`requirements.txt` changes:
```
# REMOVE:
chromadb==0.5.23          # Not used in core (FAISS is the vector store)
sqlalchemy==2.0.36        # Using raw sqlite3, not SQLAlchemy ORM
aiosqlite==0.20.0         # Same
alembic==1.14.0           # Migrations for deleted migration system
aiohttp==3.11.11          # Only needed by dashboard server
aiohttp-cors==0.7.0       # Same
apscheduler==3.10.4       # Not used in core loop

# KEEP:
openai==1.57.0
anthropic==0.40.0
httpx==0.27.2
faiss-cpu==1.9.0
numpy==1.26.4
scikit-learn==1.5.2
pyyaml==6.0.2
python-dotenv==1.0.1
rich==13.9.4
PyJWT==2.10.1             # Only if dashboard kept with auth
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
```

### 1.10 Clean Up Docs

- Delete `docs/GDIL_README.md`
- Delete `docs/PEER_SETUP.md`
- Delete `docs/Repository-Structure.md` (will be outdated)
- Delete `CONTRIBUTING.md` (premature for a solo project refocusing)
- Delete `SECURITY_REPORT.md`, `SECURITY.md` (security module deleted)
- Delete `CHANGELOG.md` (reset for refocus)
- Keep `README.md` (rewrite in Phase 2)
- Keep `docs/QUICKSTART.md` (update in Phase 2)
- Keep `docs/system-arch.md` (update in Phase 2)
- Keep `SPEC_SHEET.md` (update in Phase 2)

### Post-Cut File Count

**Before:** ~48 Python files, ~6,800 lines
**After:** ~20 Python files, ~3,000 lines

**Remaining structure:**
```
synth-mind/
├── run_synth.py
├── requirements.txt
├── config/personality.yaml
├── core/
│   ├── orchestrator.py      (slimmed ~400 lines)
│   ├── llm_wrapper.py       (unchanged)
│   ├── memory.py            (unchanged)
│   └── tools.py             (slimmed ~500 lines)
├── psychological/
│   ├── predictive_dreaming.py
│   ├── assurance_resolution.py
│   ├── meta_reflection.py
│   ├── temporal_purpose.py
│   └── reward_calibration.py
├── utils/
│   ├── emotion_regulator.py
│   ├── metrics.py
│   ├── logging.py
│   └── mandelbrot_weighting.py
├── dashboard/               (simplified)
│   ├── server.py
│   └── dashboard.html
├── tests/
│   ├── conftest.py
│   ├── test_core_modules.py
│   ├── test_psychological_modules.py
│   └── test_mandelbrot_e2e.py
└── docs/
    ├── QUICKSTART.md
    └── system-arch.md
```

---

## PHASE 2: FIX (Make the psychology layer actually work)

Goal: Every psychological module should produce a *measurable, testable* change in LLM output. No more numeric theater.

### 2.1 Rebuild EmotionRegulator

**Problem:** `utils/emotion_regulator.py` is a single float (`current_valence += delta`). Mood tags are cosmetic. Nothing downstream reads them meaningfully.

**Fix:** Implement the PAD model the SPEC_SHEET.md already describes:

```
emotion_state = {
    valence: float,      # pleasure/displeasure (-1 to 1)
    arousal: float,      # calm/excited (-1 to 1)
    dominance: float     # submissive/dominant (-1 to 1)
}
```

Each dimension should independently influence response generation:
- **Valence** affects tone (warm vs. cautious) via system prompt injection
- **Arousal** affects verbosity and creativity (temperature + max_tokens)
- **Dominance** affects assertiveness (hedging language, confidence level)

**Key change:** `EmotionRegulator.get_system_prompt_modifier()` returns a string that gets injected into every LLM call's system prompt. This is how emotion actually reaches the output.

### 2.2 Rebuild TemporalPurposeEngine

**Problem:** Narrative evolution is `self.narrative_summary += new_element` with `[-400:]` truncation. The comment says "In production: use LLM to synthesize." It's time.

**Fix:**
- `incorporate_reflection()` calls `self.llm.generate()` to synthesize the old narrative + new insight into a coherent updated narrative (max 300 words)
- Store narrative versions with timestamps for drift analysis
- `current_narrative_summary()` returns a narrative that's actually read by the system prompt builder in the orchestrator
- Self-schema embedding updates on every narrative change, enabling real drift detection

### 2.3 Fix MetaReflection Fallbacks

**Problem:** `_parse_reflection()` returns hardcoded `coherence_score: 0.8` when parsing fails, making reflection always "succeed."

**Fix:**
- On parse failure, return `None` and handle gracefully upstream
- Add retry logic: if JSON parse fails, ask the LLM to reformat
- Track parse failure rate as a real metric
- When coherence *actually* drops below threshold, inject specific corrective instructions into the system prompt (not just appending "(Taking a moment to recalibrate...)")

### 2.4 Fix AssuranceResolution Stubs

**Problem:** `assurance_success_rate()` returns `0.85` always. The Query Rating system logs uncertainties but never uses them.

**Fix:**
- Compute real success rate from `uncertainty_log` table (resolved / total)
- Use logged uncertainty patterns to adjust hedge word detection thresholds
- When uncertainty is high, *actually modify the response* - add caveats, ask clarifying questions, or refuse to answer confidently

### 2.5 Fix RewardCalibration Signals

**Problem:** `context_load` signal checks `hasattr(self.memory, 'context')` which never exists. Always returns 0.

**Fix:**
- Use `self.memory.current_turn` and recent turn count as context load proxy
- Make temperature adjustment range wider (0.3-1.0 instead of 0.4-1.2) so flow state effects are actually perceptible
- Log difficulty estimates against user satisfaction to validate the model

### 2.6 Wire Psychology Into System Prompt

**This is the most important change.** Currently the psychological pipeline runs *alongside* generation but barely touches it. The only influence path is temperature adjustment.

**Fix:** Build a `SystemPromptBuilder` in the orchestrator:

```python
async def _build_system_prompt(self) -> str:
    """Compose system prompt from all psychological modules."""
    sections = []

    # 1. Base personality
    sections.append(self._get_personality_prompt())

    # 2. Emotional state influence
    emotion_modifier = self.emotion.get_system_prompt_modifier()
    if emotion_modifier:
        sections.append(emotion_modifier)

    # 3. Current narrative / identity
    narrative = self.temporal.current_narrative_summary()
    sections.append(f"Your current self-understanding: {narrative}")

    # 4. Dream predictions context (what you anticipated)
    if self.dreaming.dream_buffer:
        top_dream = max(self.dreaming.dream_buffer, key=lambda d: d['prob'])
        sections.append(
            f"You anticipated the user might say something like: '{top_dream['text']}'. "
            f"Adapt if reality differs."
        )

    # 5. Recent reflection insights
    if self.reflection.reflection_log:
        last = self.reflection.reflection_log[-1]
        insight = last.get('reflection', {}).get('overall_insight', '')
        if insight:
            sections.append(f"Recent self-insight: {insight}")

    # 6. Assurance level
    uncertainty = self.assurance.recent_uncertainty_avg()
    if uncertainty > 0.7:
        sections.append(
            "You are uncertain about recent interactions. "
            "Be more careful, ask clarifying questions, hedge appropriately."
        )

    return "\n\n".join(sections)
```

Then in `_process_turn()`, pass this to `self.llm.generate()` as the `system` parameter:

```python
system_prompt = await self._build_system_prompt()
draft_response = await self.llm.generate(
    context_str,
    temperature=self.calibration.creativity_temperature,
    system=system_prompt
)
```

This single change makes every psychological module's state *directly influence the LLM's behavior*.

### 2.7 Implement Background Consolidation

**Problem:** `_background_consolidation()` is an empty loop.

**Fix:** Every hour (or after N turns):
- Run `memory.detect_coherence_drift()` and log results
- Compress old episodic memories into semantic summaries
- Update temporal narrative based on accumulated session data
- Save Mandelbrot corpus to disk

### 2.8 Update run_synth.py Banner

Remove references to deleted commands (`/project`, `/collab`, `/vcs`, `/templates`). Add any new commands from Phase 2 changes.

---

## PHASE 3: PROVE (Build evaluation framework)

Goal: Empirically answer: *"Does the psychological pipeline produce better conversations than a bare LLM wrapper?"*

### 3.1 Build A/B Eval Harness

Create `eval/` directory with:

```
eval/
├── baseline.py          # Bare LLM wrapper (no psychology)
├── synth_eval.py        # Full Synth Mind pipeline
├── scenarios.py         # Test conversation scripts
├── judge.py             # LLM-as-judge evaluation
└── results/             # Stored eval results
```

**baseline.py**: Same LLM, same memory for context, but NO emotional state, NO dreaming, NO reflection, NO calibration. Just `llm.generate(context)`.

**scenarios.py**: 20-30 scripted multi-turn conversations covering:
- Emotional support (user is frustrated, sad, excited)
- Long-running topic (coherence over 15+ turns)
- Ambiguous questions (should trigger assurance)
- Topic pivots (should trigger dreaming mismatch)
- Identity questions ("who are you?" across sessions)

**judge.py**: Use a separate LLM call to rate both responses on:
- Coherence (1-5)
- Empathy (1-5)
- Helpfulness (1-5)
- Personality consistency (1-5)
- Naturalness (1-5)

### 3.2 Integration Tests That Matter

Replace the current shallow tests with pipeline tests:

```python
async def test_emotion_affects_output():
    """Verify that emotional state changes produce different responses."""
    orchestrator_happy = SynthOrchestrator()
    orchestrator_happy.emotion.current_valence = 0.8

    orchestrator_sad = SynthOrchestrator()
    orchestrator_sad.emotion.current_valence = -0.8

    response_happy = await orchestrator_happy._process_turn("How are you?")
    response_sad = await orchestrator_sad._process_turn("How are you?")

    # Responses should be meaningfully different
    assert response_happy != response_sad
    # Judge: happy response should score higher on warmth
```

```python
async def test_dreaming_improves_alignment():
    """Verify dreams improve next-turn response relevance."""
    # Run 10 turns with dreaming enabled vs disabled
    # Measure response relevance scores
    # Dreaming-enabled should show higher alignment
```

```python
async def test_reflection_corrects_drift():
    """Verify reflection catches and corrects topic drift."""
    # Gradually introduce off-topic turns
    # Verify reflection triggers and adjusts behavior
```

### 3.3 Metrics Dashboard

Simplify `dashboard/dashboard.html` to show the metrics that actually matter post-refocus:

1. **Emotional State** - PAD model visualization (3 gauges)
2. **Dream Alignment** - Rolling average of prediction accuracy
3. **Assurance Level** - Current uncertainty + real resolution rate
4. **Narrative** - Current self-narrative text
5. **Flow State** - Difficulty estimate + temperature
6. **A/B Score** - Running eval comparison vs. baseline

Remove the 8-card layout. Show what's real.

---

## EXECUTION ORDER

**Week 1: Cut**
1. Delete all files in 1.1 and directories in 1.1
2. Edit orchestrator per 1.2
3. Delete social_companionship.py (Option A in 1.3)
4. Delete goal_directed_iteration.py (Option A in 1.4)
5. Simplify tools per 1.5
6. Clean dashboard per 1.6
7. Clean config, tests, deps, docs per 1.7-1.10
8. Verify `python run_synth.py` still starts (with mock LLM)
9. Verify `pytest tests/` passes

**Week 2: Fix Core**
1. Rebuild EmotionRegulator with PAD model (2.1)
2. Build SystemPromptBuilder (2.6) - this is the highest-impact change
3. Fix RewardCalibration signals (2.5)
4. Fix AssuranceResolution stubs (2.4)

**Week 3: Fix Identity**
1. Rebuild TemporalPurposeEngine with LLM synthesis (2.2)
2. Fix MetaReflection fallbacks (2.3)
3. Implement background consolidation (2.7)
4. Update banner and commands (2.8)

**Week 4: Prove**
1. Build A/B eval harness (3.1)
2. Write integration tests (3.2)
3. Run first eval round
4. Update dashboard (3.3)
5. Document results in README

---

## SUCCESS CRITERIA

The refocus succeeds if:

1. **Quantitative:** Synth Mind responses score >= 15% higher than bare LLM baseline on the A/B eval across empathy, coherence, and personality consistency dimensions.

2. **Qualitative:** A human evaluator can identify which response comes from Synth Mind vs. baseline in >= 70% of cases (above chance).

3. **Technical:** Every psychological module has at least one integration test proving it changes LLM output. No hardcoded fallbacks that silently "succeed." No stubs returning fake metrics.

If these criteria aren't met after Phase 3, the project's core hypothesis is invalidated and should be abandoned or fundamentally reconceived.
