# Security

Two things here are worth stating plainly: what this project sends to
third-party model providers, and how its API keys are handled.

## What data is involved

**No patient data.** The inputs are clinical trial *eligibility criteria* —
the protocol text describing who may enrol in a study — sourced from
ClinicalTrials.gov, a public registry. They describe rules, not people.
Nothing under `sample_data/` or `ref/` is PHI, and the project has no
mechanism for ingesting a patient record.

That is worth being explicit about, because the surrounding vocabulary
(clinical, criteria, traits, reviewers) reads like a system that handles
patient data. It does not.

## Model providers

Decomposition and LLM-based agreement analysis send criteria text to whichever
provider is configured — OpenAI, Google Gemini, or Anthropic — via LangChain.
Because the text is public registry content, this is not a PHI disclosure.
It is still a third-party API call, so normal considerations apply: provider
terms, cost, and rate limits.

If you extend this to any non-public criteria source, re-evaluate that. The
code will happily send whatever JSON you point it at.

## API keys

Keys live in `api_keys.json`, which is **gitignored**. `api_keys_template.json`
is the committed template and contains placeholders only.

```sh
cp api_keys_template.json api_keys.json   # then fill in your keys
```

Specifics:

- `api_keys.json` is read at runtime by `services/api_key_service.py`. It is
  never written to, logged, or echoed.
- The template's placeholder values (`<OPENAI_API_KEY>` and friends) are not
  credentials. Neither are the illustrative `sk-ant-...` strings in the
  documentation.
- LangSmith tracing, when enabled, sends prompts and responses to
  LangSmith. Its key lives in the same file. See
  `docs/setup/LANGSMITH_SETUP.md`.
- Rotate any key that has appeared in a shell history, a notebook output, or
  a screen share.

**Before committing**, confirm your keys are not staged:

```sh
git status --porcelain | grep api_keys.json   # should print nothing
```

## Caching

`services/cache_service.py` enables a LangChain SQLite cache at
`.langchain.db` (gitignored). It stores prompts and completions in plain text
on disk so repeated runs do not re-bill. Delete the file to clear it. If you
run against criteria you consider sensitive, treat that database as sensitive
too.

## Cost

There is no spend cap. `experiments/batch_run_decompose_criteria.py` will
iterate a whole cohort across multiple providers, and
`experiments/cost_calculator.py` exists precisely because those runs are not
free. Check the estimate before launching a batch.

## Reporting a vulnerability

Open a GitHub issue for anything non-sensitive. For anything involving
credentials, contact the maintainer directly rather than filing publicly, and
include reproduction steps and the commit SHA.
