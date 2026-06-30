# DataForge 🛠️

Premium AI-Powered Data Quality & Standardization Engine

A production-grade web application for profiling, cleaning, validating, and enriching messy datasets. Automates repetitive data work while maintaining full transparency and control.

---

## Features

- **📊 In-Depth Schema Profiling:** Semantic datatype inference (Numeric, Categorical, Date, Boolean, Text) with completeness analytics

- **🚨 Outlier & Anomaly Scanning:** IQR-based numerical outliers, rare categories, format deviations (email, phone regex validation)

- **🛠️ Configurable Tabular Cleaning:** Header standardization, whitespace trimming, duplicate removal, and intelligent imputation (Mean, Median, Mode, Constant)

- **🔀 Fuzzy Deduplication:** Text similarity clustering using RapidFuzz Levenshtein distance to group and standardize records

- **🧠 AI-Assisted Operations:**
  - Semantic Column Inference: Rename cryptic headers using LLM context
  - Intelligent Value Normalization: Standardize messy descriptors across datasets

- **🛡️ Custom Validation Rules:** Assert ranges, non-nulls, unique IDs, regex patterns, enum constraints

- **💾 Rich Exports:** Download cleaned CSV/JSON + comprehensive quality reports

---

## Architecture

Decoupled three-tier design: **Streamlit frontend** → **API layer** → **Core processors**

### Backend Processors

- **schema_inference.py** – Semantic type detection beyond primitives
- **cleaner.py** – Deterministic tabular transformations
- **fuzzy_matcher.py** – Levenshtein-based clustering with fallback
- **llm_integrations.py** – Anthropic Claude & Google Gemini adapters with graceful offline mode
- **anomaly_detector.py** – Statistical outlier detection
- **validators/rules.py** – OOP-based rule evaluation

### Production Quality

✅ Comprehensive test suite (Pytest) with fixtures  
✅ Type hints throughout (typing module)  
✅ Error handling & graceful degradation  
✅ Logging & structured output  
✅ Docker & CI/CD ready  
✅ Zero hard dependencies on LLM APIs (fallback heuristics included)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or 3.11
- Pip package manager
- (Optional) Docker for containerized deployment
- (Optional) API keys for Claude & Gemini

### Local Development Setup

**1. Clone & install dependencies:**

```bash
git clone https://github.com/yourusername/DataForge.git
cd DataForge
pip install -r requirements.txt
```

**2. Configure API keys (optional for LLM features):**

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"
export GEMINI_API_KEY="your-gemini-key"
```

*Note: DataForge works offline with heuristic fallbacks if keys are absent. You can still use schema profiling, cleaning, validation, and deduplication.*

**3. Run the application:**

```bash
streamlit run frontend/app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

**4. Run tests:**

```bash
python3 -m pytest backend/tests/ -v
```

### Docker Deployment

**1. Build the image:**

```bash
docker build -t dataforge:latest .
```

**2. Run the container:**

```bash
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY="your-key" \
  -e GEMINI_API_KEY="your-key" \
  dataforge:latest
```

Access at [http://localhost:8501](http://localhost:8501).

### Streamlit Cloud Deployment

1. Push repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select "New app" and connect your repo
4. Set entry point to `frontend/app.py`
5. Add API keys in **Settings** → **Secrets management**
6. Click **Deploy**

---

## 📋 Usage Workflow

### Step-by-Step

1. **Upload** – Drop CSV/XLSX/JSON files via the UI
2. **Profile** – View schema detection, data completeness, anomaly flags
3. **Configure** – Add cleaning rules, fuzzy matching groups, validation constraints
4. **Preview** – See before/after transformations side-by-side
5. **Validate** – Run custom rules, review failures with row-level detail
6. **Export** – Download cleaned data (CSV/JSON) + quality report (JSON)

### Example: Cleaning Fashion BOM Data

```
1. Upload: supplier_bom.xlsx
   ↓
2. Profile: Detects 12% null rate in "Material", typos in supplier names
   ↓
3. Configure: 
   - Standardize headers: "Ctn Wgt" → "carton_weight_grams"
   - Normalize materials: "Org. Cotton (GOTS)" → "organic_cotton"
   - Fill missing weights: Mean imputation
   - Deduplicate suppliers: Group "H&M Ltd" + "H and M Mfg"
   ↓
4. Preview: See corrected rows
   ↓
5. Validate: Assert carton_weight > 0, supplier is unique
   ↓
6. Export: cleaned_bom.csv + quality_report.json
```

---

## 🛠️ Technologies

**Backend:**
- Python, Pandas, NumPy
- RapidFuzz (fuzzy matching)
- Anthropic SDK (Claude API)
- Google Genai SDK (Gemini API)

**Frontend:**
- Streamlit (interactive UI)
- Altair (charting)

**Testing & Deployment:**
- Pytest (unit tests)
- Docker (containerization)
- GitHub Actions (CI/CD ready)

---

## 📊 Use Cases

✓ **Fashion/Retail** – Normalize BOMs, catalogs, supplier data  
✓ **Healthcare** – Standardize patient records, medical terminology  
✓ **Manufacturing** – Reconcile part specifications across suppliers  
✓ **Finance** – Dedup transaction records, standardize GL codes  
✓ **Logistics** – Unify shipping/tracking data formats

---

## 🧪 Testing

Run the full test suite:

```bash
pytest backend/tests/ -v
```

Run specific test file:

```bash
pytest backend/tests/test_cleaner.py -v
```

Run with coverage:

```bash
pytest backend/tests/ --cov=backend --cov-report=html
```

---

## 📁 Project Structure

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
│   │   └── llm_integrations.py  # Claude & Gemini wrappers
│   ├── validators/
│   │   └── rules.py         # Rule checking logic classes
│   └── tests/               # Pytest suite
│       ├── test_cleaner.py
│       ├── test_fuzzy.py
│       ├── test_validators.py
│       └── fixtures/
├── frontend/
│   ├── app.py               # Main layout page
│   ├── styles.py            # Global custom style injections
│   └── pages/
│       ├── 1_Upload.py      # File drop & metadata preview
│       ├── 2_Profile.py     # Schema stats, graphs, & anomalies
│       ├── 3_Clean.py       # Transforming, fuzzy standardizing
│       └── 4_Report.py      # Rules builder & validation
├── docs/
│   ├── README.md
│   └── ARCHITECTURE.md
├── requirements.txt
├── Dockerfile
├── .github/
│   └── workflows/
│       └── tests.yml        # CI/CD pipeline
└── .gitignore
```

---

## 🔐 Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Optional | Enable Claude for column inference & normalization |
| `GEMINI_API_KEY` | Optional | Enable Gemini as alternative LLM |

If neither is set, DataForge uses offline heuristic matching.

---

## 🤝 Contributing

Contributions welcome! Areas for enhancement:

- Additional data formats (Parquet, HDF5, databases)
- Custom ML-based anomaly detection
- Batch processing pipelines (Airflow, Prefect integration)
- Advanced deduplication strategies
- Multi-language support

---

## 📝 License

MIT License – See LICENSE file for details

---

## 🙋 Support & Feedback

Found a bug or have a feature request? Open an issue on GitHub.

For questions about the architecture, see [ARCHITECTURE.md](./docs/ARCHITECTURE.md).

---

## 💡 Why DataForge?

Most data science work isn't algorithms—it's data cleaning. DataForge automates the tedious parts (parsing, normalizing, validating) while keeping humans in control. It's built for real teams solving real data problems, not for research or demonstrations.

**Ship with confidence.** 🚀
