# System Architecture - DataForge 🛠️

DataForge is architected with a decoupled structure separating backend computational engines, API endpoints, and the Streamlit frontend. This allows developers to export the backend modules as a standalone library or integration within larger automated pipelines (e.g. Airflow or Prefect) without visual coupling.

---

## Architecture Blueprint

```
                     ┌────────────────────────┐
                     │ Streamlit Frontend UI  │
                     │ (app.py, subpages)     │
                     └───────────┬────────────┘
                                 │ Ingests / Invokes
                                 ▼
                     ┌────────────────────────┐
                     │     API Layer /        │
                     │  Interface Functions   │
                     │   (backend/api/*)      │
                     └───────────┬────────────┘
                                 │ Orchestrates
                                 ▼
         ┌───────────────────────┴───────────────────────┐
         │              Core Processors                  │
         │             (backend/core/*)                  │
         ├───────────────────────┬───────────────────────┤
         │                       │                       │
         ▼                       ▼                       ▼
 ┌──────────────┐        ┌──────────────┐        ┌───────────────┐
 │ Schema       │        │ Tabular      │        │ AI Engine     │
 │ Inference &  │        │ Cleaner &    │        │ Normalization │
 │ Anomalies    │        │ Fuzzy Match  │        │ (Gemini/      │
 │ Scanner      │        │ Engine       │        │ Claude)       │
 └──────────────┘        └──────────────┘        └───────────────┘
```

---

## Component Specifications

### 1. Schema Inference Engine (`schema_inference.py`)
- Analyzes Series distributions to infer semantic types beyond standard primitive Pandas types.
- Evaluates:
  - **Boolean:** Checked by verifying whether non-null card belongs to known indicator pairs (`y/n`, `active/inactive`, `1/0`).
  - **Numeric:** Evaluates float or integer casts.
  - **Datetime:** Uses standard date regex pattern scans (e.g. `YYYY-MM-DD`, `MM/DD/YYYY`) before converting via `pd.to_datetime` to ensure high parsing confidence.
  - **Categorical:** Flagged if cardinality (number of unique categories) is low relative to data scale (e.g. unique values <= 15 or < 15% of records).
  - **Text:** Default fallback for string streams.

### 2. Tabular Cleaner (`cleaner.py`)
- Executes transformations sequentially using a pipeline JSON structure.
- Supported operations:
  - **Header Standardization:** Programmatic snake_case, camelCase, uppercase transformations.
  - **Whitespace Trimming:** Removes noise padding from object columns.
  - **Imputations:** Imputes numerical missingness using Mean/Median, and categorical missingness using Mode or user-specified Constants.
  - **Type Castings:** Handles conversions between primitives and pandas nullable datatypes (e.g. nullable integers `"Int64"` and nullable booleans `"boolean"`).

### 3. Fuzzy Clustering Engine (`fuzzy_matcher.py`)
- Leverages Levenshtein distance metrics (from `rapidfuzz` if present, falling back to python's standard `difflib.SequenceMatcher` to support zero-dependency setups).
- Groups near-duplicate categories using frequency sorting, placing the most common values at the center of the clusters (treated as the canonical standard representation).

### 4. AI Orchestrator (`llm_integrations.py`)
- Interfaces with the new `google-genai` SDK (targeting `gemini-2.5-flash` for high throughput) and the `anthropic` SDK (targeting `claude-3-5-sonnet` for heavy reasoning).
- Includes deterministic local heuristic catalog mapping fallback methods. If no API keys are loaded, DataForge uses pre-defined dictionaries to map common industry schemas (e.g. fashion materials like `"Org. Cotton"` &rarr; `"organic_cotton"` or headers like `"Ctn Wgt"` &rarr; `"carton_weight_grams"`), allowing the user to experience the full workflow without active API connectivity.

### 5. Custom Rules Engine (`validators/rules.py`)
- Implements validators using object-oriented rule classes.
- Validates columns against range intervals, non-nulls, unique primary keys, regex patterns, or allowed enumerations.
- Formulates a standardized validation failure log representing errors and row indexes.

---

## Data Pipeline Flow

1. **Ingestion:** File uploaded &rarr; `backend/api/upload.py` parses stream &rarr; Session State.
2. **Analysis:** `backend/api/profile.py` computes metrics and flags outliers &rarr; Dashboard.
3. **Configuration:** Users add cleaning rules, check fuzzy spellings, and generate LLM translation mappings.
4. **Execution:** Rules compiled into pipeline configuration dict &rarr; `backend/api/clean.py` executes sequential transforms &rarr; Returns clean dataset.
5. **Assertion:** Clean dataset checked by `backend/api/validate.py` against rules &rarr; Outputs final quality report and download bundles.
