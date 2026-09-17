# Contributing

## Setup

**Prerequisites:** Python 3.10+ and, for the web UI, Node.js 20+.

```sh
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install pytest

cp api_keys_template.json api_keys.json   # fill in keys — gitignored
```

Run the tests:

```sh
pytest tests/ -q          # or: python tests/run_tests.py
```

**The test suite needs no API keys and contacts no model provider.** Only
`decompose_criteria.py` and the LLM path of the agreement analysis do.

### Dependency pins are load-bearing

`requirements.txt` pins LangChain to the 0.3 line with upper bounds. This is
not caution for its own sake: the pins were previously absent, pip resolved
langchain 1.x, and `services/cache_service.py` failed at import because
`langchain.globals` no longer exists there. Nothing in the project would
start from a clean install.

If you need a newer LangChain, treat it as a migration — `langchain.globals`,
`langchain.chat_models.init_chat_model`, and `langchain_community.cache` all
moved in 1.x — not a version bump. CI installs from `requirements.txt` on
Python 3.10, 3.11, and 3.12 and imports every top-level module before running
a single test, so this class of breakage fails loudly.

### Web UI

```sh
# backend — http://localhost:5000
cd webui/backend && pip install -r requirements.txt && python app.py

# frontend — http://localhost:3000
cd webui/frontend && npm ci && npm run dev
```

The frontend reads `NEXT_PUBLIC_API_BASE_URL`, defaulting to
`http://localhost:5000`.

---

## Before you push

```sh
pytest tests/ -q
cd webui/frontend && npm run lint && npm run build
python .github/scripts/smoke_backend.py    # run from webui/backend/
```

That is what CI runs.

---

## Conventions

**Branches.** `feat/…`, `fix/…`, `docs/…`, `refactor/…`, `test/…`.

**Commits.** `<type>(<scope>): <summary>`, imperative, under ~72 chars. The
body explains *why* — the diff already shows what.

**Schemas are the contract.** The Pydantic models in `schemas/` define what
decomposition emits and what the agreement analysis consumes. Changing one is
a breaking change with three downstream consumers that will not fail at
import time:

1. `tests/` construct the models directly.
2. `webui/frontend/src/lib/types.ts` mirrors the JSON shape.
3. Previously generated output under `sample_data/` no longer matches.

Search for the field name across all three before you rename it. The project
has already been through one such refactor where the tests and the web UI
were left behind — see the "known gaps" section of the README.

**Tests.** Match the existing style: `unittest.TestCase` classes, discovered
by pytest. Keep them hermetic — mock `ChainService`/`LLMService` rather than
calling a provider. `tests/test_fleiss_kappa.py` is the model to follow for
anything numeric: every expected value is derived by hand from the definition
rather than recorded from a run, so the test fails when the computation
changes rather than merely tracking it.

**Adding a model provider.** `services/llm_service.py` is the seam. Add the
provider there and to `api_keys_template.json`; nothing else should need to
know which provider is in use.
