# Smart Question Paper Generator (Science) — Evalvia Intern Assignment

A tool that generates a Science question paper from total marks, difficulty
mix, topic weightage, and question-type mix — the way a teacher actually
builds one — and shows the resulting breakdown, including exactly where
and why it couldn't hit the request perfectly.

## Stack

- **Backend:** FastAPI (Python) — the constraint engine and API
- **Frontend:** React + Tailwind — request form, generated paper view, constraint report, swap
- **Data:** a single JSON question bank, loaded into memory at startup
- **LLM:** offline enrichment script (`scripts/enrich_bank.py`) expands the seed bank; never called at runtime

## Running it

Backend:
```
cd backend
pip install fastapi uvicorn pydantic --break-system-packages
uvicorn main:app --reload --port 8000
```

Frontend:
```
cd frontend
npm install
npm run dev
```
The Vite dev server proxies `/api/*` to `http://localhost:8000` (see
`vite.config.js`), so the two just need to run side by side — no CORS
setup needed beyond what's already in `main.py`.

## Project structure

```
backend/
├── main.py                 # FastAPI routes — thin, no business logic
├── models.py                # Pydantic schema for everything
├── data/
│   └── question_bank.json   # seed + LLM-enriched Science questions
├── scripts/
│   └── enrich_bank.py       # offline LLM expansion of the seed bank
├── engine/
│   ├── validator.py         # Stage 0 — input validation
│   ├── feasibility.py       # Stage 2 — bank supply vs. requested targets
│   ├── matrix_fit.py        # Stage 3 — capped IPF target matrix
│   ├── selector.py          # Stage 4 — fills the matrix with real questions
│   ├── resolver.py          # Stage 5 — builds the honest constraint report
│   ├── composer.py          # Stage 6 — sections, ordering, interleaving
│   └── swap.py               # Stage 7 — single-question swap
frontend/
├── index.html
├── package.json
├── vite.config.js
└── src/
    ├── main.jsx
    ├── App.jsx
    ├── api.js
    ├── index.css
    └── components/
        ├── ConstraintForm.jsx
        ├── PaperView.jsx
        ├── QuestionCard.jsx
        └── ConstraintReport.jsx
```

## Assumptions

- **Marks scheme:** MCQ = 1 mark, Short Answer = 3 marks, Long Answer = 5
  marks. Chosen for a clean split across three sections and enough
  granularity (1/3/5) that exact-total reconciliation is usually possible
  using MCQs as the fine-tuning unit.
- **Subject scope:** Science only (Physics, Chemistry, Biology), per the
  assignment's option to focus on one subject.
- **Percentages are computed against total marks**, not question count, and
  the generated paper always matches the requested total exactly whenever
  the bank makes that possible (see below for when it isn't).
- **Question bank size:** 46 hand-written questions, with a deliberately
  thin pool for Physics/Hard (9 marks total, vs. 13–18 for every other
  topic/difficulty cell) so the constraint engine has a real, demonstrable
  scarcity case rather than a hypothetical one.

## Approach — pure logic, and why

The entire constraint engine (Stages 0–7) is deterministic Python — no LLM
calls at runtime. This was a deliberate choice, not a default:

- **Auditability.** A teacher (or a grader) needs to trust *why* a paper
  came out the way it did. A deterministic pipeline can point to an exact
  cell, an exact shortfall, an exact substitution. An LLM making runtime
  selection decisions can't be interrogated that way, and would risk
  silently inventing a plausible-sounding but wrong justification.
- **Reproducibility.** The same request with the same seed always produces
  the same paper. That matters for debugging, for grading, and for a
  teacher who wants to regenerate deliberately rather than by chance.
- **The problem is genuinely a constraint-satisfaction problem**, not a
  generation problem — three marginal distributions intersecting over a
  finite bank is a solved category of problem (transportation / IPF /
  apportionment), and reaching for an LLM to approximate it would be worse
  on every axis: slower, non-reproducible, harder to test, and no more
  correct.

**Where an LLM *would* fit** (not yet implemented — see below): offline
enrichment of the question bank itself — generating more phrasings,
subtopics, and difficulty variants from the 46 seed questions, so the
constraint engine has a richer pool to work with. That's a data-generation
problem, which LLMs are well suited to, kept entirely separate from the
runtime decision-making, which they are not.

## How "constraints don't fit" is handled

This is the actual hard part of the assignment, and it's handled in layers
rather than one big check:

1. **Feasibility check (Stage 2)** runs *before* any question is picked,
   comparing requested marks against real bank supply at three levels: per
   topic, per difficulty, per qtype, and per (topic, difficulty, qtype)
   cell. Every genuine shortfall is recorded as a `Gap` with a concrete
   reason — nothing is discovered mid-generation.
2. **Matrix fitting (Stage 3)** uses a capped version of Iterative
   Proportional Fitting to compute the best achievable
   (topic × difficulty × qtype) marks matrix, clipping every cell to real
   supply during the fit itself — so the "ideal" target the selector works
   toward is already constraint-aware, not aspirational.
3. **Selection (Stage 4)** fills that matrix with real questions, and
   redistributes any remaining shortfall to the closest substitute cell, in
   a documented priority order:

   **Total marks > Topic weightage > Question-type mix > Difficulty mix**

   Reasoning: total marks is graded against a fixed scale and must be
   exact. Topic weightage is usually syllabus-mandated by the school —
   the most rigid *pedagogical* constraint after marks. Question-type mix
   is a formatting choice. Difficulty mix is the most negotiable — a
   paper slightly easier or harder than requested is a smaller problem for
   a teacher than one that under-represents a mandated topic or misses the
   total. Concretely: a shortfall is first absorbed by shifting difficulty
   within the same topic, before it's ever allowed to shift topic.
4. **Reporting (Stage 5)** never stays silent about a deviation. Every gap
   above a small tolerance becomes a `Deviation` with requested %, actual
   %, and — critically — an *honest* cause: it only blames "bank limit"
   when there's real evidence (a feasibility gap, an unmet cell, a logged
   substitution); otherwise it correctly attributes the gap to the
   selection algorithm's own trade-offs (see the bug log below). Rejecting
   the request outright was considered and rejected as a design: a teacher
   gets more value from a transparent best-effort paper with a clear
   report than from a bare error message.

## Question swap

A swap never re-runs the full pipeline — it's an isolated, near-instant
lookup (`engine/swap.py`, `POST /swap`). It tries, in order: an exact
same-topic/same-difficulty/same-qtype match; same topic with adjacent
difficulty; same difficulty with a different topic; any cell with the same
qtype. It never falls back to a different qtype, because that would
silently change the question's marks value and therefore the paper's
total — swap preserves total marks unconditionally. If nothing is left
anywhere in the bank for that qtype, it fails with a specific, actionable
explanation rather than duplicating a question or crashing.

## Bugs caught during development (kept in, not smoothed over)

Testing each stage in isolation surfaced two real problems worth
documenting rather than hiding:

1. **Feasibility false positives.** The first version of the cell-level
   feasibility check flagged sub-question-sized rounding gaps as
   "infeasible" even on a perfectly satisfiable request. Fixed by only
   surfacing a cell gap when the shortfall is at least one whole
   question's worth of marks.
2. **A real marks-loss bug in selection.** Rounding each of the 27
   (topic × difficulty × qtype) cells to the nearest question
   *independently* silently discarded ~30% of the total marks on a typical
   request, because most individual cell targets fall below one question's
   value when split 27 ways. This is exactly the "silently ignoring the
   constraint" failure the assignment warns against, just hiding one layer
   deeper than the obvious case. Fixed with a largest-remainder
   apportionment pass (the same method used to fairly allocate
   parliamentary seats from vote shares): floor every cell, then hand the
   recovered marks to the cells with the largest leftover fraction first.

## Where it falls short, and what I'd do with more time

- **Selector Pass 2 still drifts on individual axes.** The largest-remainder
  bump-up (above) correctly fixes the *total*-marks loss, but it ranks
  candidate bumps by each cell's own fractional remainder, not by combined
  distance-to-target across all three axes at once. In testing, this
  produced 8–12 percentage-point swings on individual topic/qtype shares
  even when the bank had zero real scarcity. The resolver now reports this
  honestly (see bug log) rather than mislabeling it as a bank limit, but
  the underlying algorithm should be improved to rank bumps by combined
  cross-axis error, not just local remainder.
- **Bank enrichment hasn't actually been run.** `scripts/enrich_bank.py`
  is written and its merge/validation logic is tested (with a fake model
  function standing in for the real API call, since this environment has
  no `ANTHROPIC_API_KEY`), but it hasn't been run against the live
  Anthropic API, so the bank shipped here is still the 46 hand-written
  seed questions only.
- **In-memory paper storage.** `PAPERS` lives in a Python dict in
  `main.py`; a restart loses every generated paper. Fine for this
  assignment's scope, not production-ready.
- **`/paper/{id}` after a swap** rebuilds the constraint report using an
  empty feasibility/matrix pair, reasoning that a swap can only substitute
  within the same qtype and so can't introduce a new feasibility gap. This
  is a deliberate simplification for scope, not an oversight, but a more
  thorough version would recompute feasibility against the live bank.
- **No screenshot of the frontend.** The React app builds cleanly
  (`npm run build`, zero errors) and the generate → swap → refetch flow is
  wired against the real API, but this environment has no way to launch a
  headless browser, so the visual layout hasn't actually been eyeballed —
  worth a quick manual check before considering the UI done.

## One thing I'm proud of

Catching the largest-remainder rounding bug through actual testing, not
code review. It didn't look like a bug — `round()` on 27 independent cells
looks completely reasonable until you run it against a real bank and see
40 marks turn into 29. Testing every stage in isolation with real data,
rather than trusting each module once it "looked right," is what caught
it — and the fix (apportionment via largest remainder) is the textbook
correct tool for exactly this class of problem.

## One thing that's still weak

The Pass 2 apportionment drift described above. It's diagnosed precisely
and honestly reported, but not yet fixed — the correct fix (rank bumps by
combined multi-axis error) is a real rewrite of the selector's
redistribution logic, not a small patch, and I ran out of scope to do it
properly rather than rushing a partial fix that might introduce a new,
less-understood bug.