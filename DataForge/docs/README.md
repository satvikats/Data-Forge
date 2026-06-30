# DataForge 🛠️

DataForge is a premium, AI-assisted data profiling, cleaning, validation, and enrichment web application. It is designed to automate the painful, repetitive aspects of data cleaning while letting data engineers and analysts inspect structural issues, test validation constraints, run fuzzy deduplication clusters, and utilize LLMs (Google Gemini & Anthropic Claude) for semantic interpretations.

---

## Features

- 📊 **In-Depth Schema Profiling:** Automated semantic datatype inference (Numeric, Categorical, Date/Datetime, Boolean, Text) alongside completeness rate analytics.
- 🚨 **Outlier & Anomaly Scanning:** Detects numerical outliers via Interquartile Range (IQR), rare categories, and structural format deviations (e.g. invalid emails or phone numbers).
- 🛠️ **Configurable Tabular Cleaning:** Add casting rules, whitespace trims, exact duplicate row removals, and missing cell imputations (Mean, Median, Mode, Constant fill).
- 🔀 **Fuzzy Deduplication:** Scans text columns for spelling variations and near-duplicates using RapidFuzz Levenshtein similarity to group and standardize records.
- 🧠 **AI-Assisted Operations:**
  - **Semantic Column Inference:** Rename cryptic headers (e.g. `"Ctn Wgt"` &rarr; `"carton_weight_grams"`) based on cell value examples.
  - **Intelligent Value Normalization:** Standardize messy category descriptors (e.g., `"Org. Cotton (GOTS Cert., India)"` &rarr; `"organic_cotton"`) based on context prompts.
- 🛡️ **Custom Validation Rules:** Assert value ranges, non-null requirements, unique IDs, regex patterns, or set membership constraints.
- 💾 **Rich Exports:** Download the cleaned CSV/JSON file and export a comprehensive Data Quality JSON assessment summary.

---

## Project Structure

```
DataForge/
├── backend/
│   ├── api/
│   │   ├── upload.py        # Data loader wrappers
│   │   ├── profile.py       # Statistics aggregations
│   │   ├── clean.py         # Pipeline runners
│   │   └── validate.py      # Rule validators
│   ├── core/
│   │   ├── schema_inference.py  # Datatype semantic engines
│   │   ├── cleaner.py           # Standard tabular transformations
│   │   ├── fuzzy_matcher.py     # RapidFuzz string similarities
│   │   ├── anomaly_detector.py  # IQR & format scanners
│   │   └── llm_integrations.py  # Claude & Gemini wrappers / fallback mocks
│   ├── validators/
│   │   └── rules.py         # Rule checking logic classes
│   └── tests/               # Pytest suite
├── frontend/
│   ├── app.py               # Main layout page
│   ├── styles.py            # Global custom style injections
│   └── pages/
│       ├── 1_Upload.py      # File drop & metadata preview
│       ├── 2_Profile.py     # Schema stats, graphs, & anomalies table
│       ├── 3_Clean.py       # Transforming, fuzzy standardizing, & AI normalization
│       └── 4_Report.py      # Rules builder, validation checks, before/after compare & download
├── docs/
│   ├── README.md
│   └── ARCHITECTURE.md
├── requirements.txt         # Package definitions
└── Dockerfile               # Container build config
```

---

## Installation & Local Setup

### Prerequisites
- Python 3.10 or 3.11
- Pip package manager

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)
To activate LLM capabilities, export the appropriate keys in your terminal environment (or enter them directly in the application's sidebar panel):
```bash
export GEMINI_API_KEY="your-gemini-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```
*Note: If keys are absent, the application gracefully operates in offline heuristic mode using rule-based catalog matchers.*

### 3. Run Streamlit Application
```bash
streamlit run frontend/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Run Pytest Suite
```bash
python3 -m pytest backend/tests/
```

---

## Running with Docker

1. **Build the container image:**
   ```bash
   docker build -t dataforge:latest .
   ```

2. **Run the container container (expose port 8501):**
   ```bash
   docker run -p 8501:8501 \
     -e GEMINI_API_KEY="your-key" \
     -e ANTHROPIC_API_KEY="your-key" \
     dataforge:latest
   ```
