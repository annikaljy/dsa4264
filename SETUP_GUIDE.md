# Complete Setup Guide - University Job Market Analysis

## ✅ What We've Created

You now have a **professional, scalable, university-standard** project structure:

```
dsa4264/
├── config.py                    # ⭐ ALL PATHS & SETTINGS HERE
├── analysis_utils.py            # Reusable analysis functions
├── requirements.txt             # Python dependencies
├── .gitignore                   # Proper data management
├── README.md                    # Full documentation
├── SETUP_GUIDE.md              # This file
│
├── notebooks/
│   ├── complete_analysis_full.ipynb     # Your original notebook
│   └── multi_school_analysis.ipynb      # NEW: Coming next
│
└── outputs/                    # ⚠️ GITIGNORED - Not in repo
    ├── processed_jobs_dual_embeddings.parquet
    ├── nus/nus-embeddings/
    ├── smu/smu-embeddings/
    ├── sutd/sutd-embeddings/
    └── analysis_results/        # Generated results go here
```

---

## 🎯 Key Improvements

### 1. **Centralized Configuration** (`config.py`)
   - ✅ All file paths in ONE place
   - ✅ All 21 degrees configured (NUS, SMU, SUTD)
   - ✅ Analysis parameters tunable
   - ✅ Helper functions for path management

### 2. **Modular Code** (`analysis_utils.py`)
   - ✅ Reusable functions (no copy-paste)
   - ✅ Cleaner notebooks
   - ✅ Easier testing & debugging
   - ✅ Industry best practice

### 3. **Proper Data Management** (`.gitignore`)
   - ✅ Large files NOT tracked in git
   - ✅ Outputs excluded from repo
   - ✅ Prof Saif gets clean code
   - ✅ Results submitted separately

### 4. **Complete Documentation** (`README.md`)
   - ✅ Setup instructions
   - ✅ Usage examples
   - ✅ Metric explanations
   - ✅ Reproducibility guidelines

---

## 🚀 How to Use

### Quick Start

```bash
# 1. Navigate to project
cd ~/dsa4264

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Test configuration
python3 config.py

# 4. Run Jupyter
jupyter notebook notebooks/
```

### Modifying Paths

**Edit `config.py`** (lines 13-20):

```python
# Use external data directory (recommended):
DATA_DIR = Path.home() / "dsa4264_data"

# Or keep in project:
DATA_DIR = PROJECT_ROOT / "outputs"
```

### Adding/Removing Degrees

**Edit `config.py`** (lines 42-130):

```python
DEGREES = {
    "nus": {
        "degrees": {
            "data_sci_analytics": {
                "name": "Data Science and Analytics",
                "category": "data_science"
            },
            # Add new degrees here
        }
    }
}
```

### Adjusting Analysis Parameters

**Edit `config.py`** (lines 151-167):

```python
THRESHOLDS = {
    "skill_vote": 0.5,           # Lower = more jobs pass threshold
    "semantic_match": 0.45,      # Lower = broader matching
    "breadth_percentile": 60     # Higher = stricter breadth criteria
}

BERTOPIC_TRIALS = 10  # Reduce to 3 for faster runs
```

---

## 📊 Analysis Workflow

### Phase 1: Global Job Market (Run Once)
```python
# In notebook:
from config import *
import analysis_utils as au

# Load jobs
jobs_df = pd.read_parquet(JOBS_PARQUET)

# Global BERTopic clustering
# ... (creates bertopic_visualizations_global/)
```

### Phase 2: Per-Degree Analysis (Loops)
```python
# Loop through all degrees
for school, degree in get_all_degrees():

    # 1. Load modules
    modules_df = au.load_degree_modules(school, degree, config)

    # 2. Calculate similarities
    sim_matrix, votes, avg_sim = au.calculate_approval_voting(...)

    # 3. Find relevant jobs
    relevant_jobs, cutoff_idx, cutoff_score = au.find_relevant_job_market(...)

    # 4. Analyze modules
    module_analysis = au.analyze_modules(...)

    # 5. Calculate metrics
    metrics = au.calculate_degree_metrics(...)

    # 6. Save results
    au.save_degree_results(school, degree, ...)
```

### Phase 3: Summary Generation
```python
# Create comparison table
summary_df = au.create_summary_table(all_results)
summary_df.to_csv(SUMMARY_OUTPUT_DIR / "comparison.csv")
```

---

## 💾 Output Structure

```
outputs/
├── bertopic_visualizations_global/   # Global job market clustering
│   ├── global_market_distance_map.html
│   ├── global_market_hierarchy.html
│   └── ...
│
├── analysis_results/                 # Per-degree analysis
│   ├── nus/
│   │   ├── data_sci_analytics/
│   │   │   ├── module_analysis_results.csv
│   │   │   ├── relevant_jobs.csv
│   │   │   └── visualizations/
│   │   ├── business_analytics/
│   │   └── ...
│   ├── smu/
│   │   ├── business/
│   │   └── ...
│   └── sutd/
│       └── ...
│
└── summary/                          # Cross-degree comparison
    ├── all_degrees_comparison.csv
    ├── category_rankings.csv
    └── representative_samples/
```

---

## 🎓 For Prof Saif

### What to Submit

1. **Git Repository** (code only):
   ```bash
   git add config.py analysis_utils.py requirements.txt
   git add .gitignore README.md notebooks/
   git commit -m "Final submission"
   git push
   ```

2. **Data Package** (separate):
   ```bash
   # Zip outputs for reference
   cd ~/dsa4264
   zip -r dsa4264_outputs.zip outputs/ -x "*.DS_Store"

   # Upload to shared drive / submit separately
   ```

3. **Final Report**:
   - Key findings with visualizations
   - Embedded summary tables
   - Reproducibility instructions

### What Prof Gets

✅ **In Git**:
- Clean, documented code
- Configuration files
- Empty folder structure
- Setup instructions

❌ **NOT in Git**:
- Large parquet files
- Generated outputs
- Temporary files

📦 **Separately**:
- Pre-computed results (for reference)
- Can re-generate by running code

---

## 🔧 Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in virtual environment:
source .venv/bin/activate

# Reinstall:
pip install -r requirements.txt
```

### "File not found" errors
```bash
# Check config paths:
python3 config.py

# Should show ✅ All required files found
```

### Out of memory
```python
# In config.py, reduce:
BERTOPIC_TRIALS = 3  # Down from 10

# Or process in batches:
degrees = get_all_degrees()[:5]  # First 5 only
```

### Slow performance
```python
# Skip detailed visualizations:
GENERATE_DETAILED_VIZ = False

# Use cached global model:
REUSE_BERTOPIC_MODEL = True
```

---

## 📝 Key Configuration Variables

### Paths (config.py lines 13-39)
- `PROJECT_ROOT` - Project directory
- `DATA_DIR` - Where data files live
- `JOBS_PARQUET` - Job embeddings file
- `SCHOOL_EMBEDDINGS` - Module embeddings by school
- `ANALYSIS_OUTPUT_DIR` - Results destination

### Degrees (config.py lines 42-130)
- 10 NUS degrees
- 6 SMU degrees
- 5 SUTD degrees
- Categorized by type (data_science, business, engineering, etc.)

### Analysis Parameters (config.py lines 151-167)
- `THRESHOLDS` - Similarity cutoffs
- `BERTOPIC_TRIALS` - Optimization iterations
- `JOB_STOPWORDS` - Words to ignore in topic modeling
- `VIZ_SETTINGS` - Plot styling

### Representative Degrees (config.py lines 169-193)
- Selected degrees for detailed reporting
- One from each category
- Multiple schools for comparison

---

## 🎨 Visualization Settings

All controlled in `config.py`:

```python
VIZ_SETTINGS = {
    "dpi": 300,                      # High-res for reports
    "figsize_default": (12, 8),      # Standard plot size
    "figsize_wide": (16, 8),         # Wide comparison plots
    "style": "whitegrid",            # Seaborn style
    "palette": "husl",               # Color scheme
    "top_n_modules": 15              # How many to show in rankings
}
```

---

## ✨ Next Steps

1. ✅ **Created**: Config, utils, docs, .gitignore
2. ✅ **Added**: Hybrid analysis (prerequisite + job alignment)
3. 🔄 **Next**: Create multi-school notebook
4. 📊 **Then**: Run full analysis
5. 📝 **Finally**: Generate final report with key findings

## 🆕 Hybrid Analysis Extension

New optional layer that combines:
- **Job alignment** (your original work)
- **Prerequisite centrality** (your friend's insight)

See **[HYBRID_ANALYSIS.md](HYBRID_ANALYSIS.md)** for complete guide.

**4-Bucket Classification**:
1. High align + high centrality = Core foundations (strongest)
2. High align + low centrality = Specialized skills (valuable but isolated)
3. Low align + high centrality = Foundational prereqs (structural importance)
4. Low align + low centrality = Peripheral modules

Enable/disable in `config.py`:
```python
HYBRID_ANALYSIS = {"enabled": True}  # Set to False to skip
```

---

## 📚 Reference

- **Config file**: `config.py` - Change paths/settings here
- **Analysis functions**: `analysis_utils.py` - Core logic
- **Full docs**: `README.md` - Comprehensive guide
- **Setup**: This file - Quick reference

---

## 🤝 Best Practices

✅ **DO**:
- Edit `config.py` for all path/parameter changes
- Use helper functions from `analysis_utils.py`
- Keep notebooks clean and readable
- Document significant findings
- Test on subset before full run

❌ **DON'T**:
- Hardcode paths in notebooks
- Copy-paste analysis code
- Commit large data files
- Skip environment validation
- Run without virtual environment

---

**Ready to proceed!** All configuration files are in place. The multi-school notebook is next.
