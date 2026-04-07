# University Degree to Job Market Analysis

## Overview

This project analyzes the alignment between university degree curricula and job market requirements across Singapore universities (NUS, SMU, SUTD). Using natural language processing, semantic embeddings, and topic modeling, we evaluate how well different degrees prepare graduates for the current job market.

## Key Features

- **Multi-University Analysis**: Comprehensive coverage of NUS, SMU, and SUTD degrees
- **Semantic Similarity**: Uses MPNet embeddings for deep semantic understanding
- **Topic Modeling**: BERTopic clustering to identify job market niches
- **Data-Driven Thresholds**: Automatic threshold detection using Kneedle algorithm
- **Module-Level Insights**: Relevance, breadth, and transferability analysis for each module
- **Approval Voting**: Skill-to-skill matching between modules and job requirements

## Project Structure

```
dsa4264/
├── config.py                      # Centralized configuration
├── requirements.txt               # Python dependencies
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
│
├── notebooks/
│   ├── complete_analysis_full.ipynb    # Original single-degree analysis
│   └── multi_school_analysis.ipynb     # NEW: Multi-school analysis
│
└── outputs/                       # ⚠️  NOT TRACKED IN GIT
    ├── processed_jobs_dual_embeddings.parquet
    ├── nus/nus-embeddings/
    ├── smu/smu-embeddings/
    ├── sutd/sutd-embeddings/
    ├── bertopic_visualizations_global/
    └── analysis_results/
        ├── nus/
        │   ├── data_sci_analytics/
        │   ├── business_analytics/
        │   └── ...
        ├── smu/
        └── sutd/
```

## Setup Instructions

### 1. Prerequisites

- Python 3.9 or higher
- 8GB+ RAM recommended (for embeddings)
- ~5GB disk space for data files

### 2. Clone Repository

```bash
git clone https://github.com/yourusername/dsa4264.git
cd dsa4264
```

### 3. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Data Setup

**⚠️ IMPORTANT**: Large data files are NOT tracked in Git. You need to obtain them separately.

#### Option A: Use Provided Data (Recommended for Reproduction)
If you received a data package (`dsa4264_data.zip`), extract it:

```bash
# Extract to project directory
unzip dsa4264_data.zip -d outputs/
```

#### Option B: External Data Directory (Recommended for Development)
To keep data separate from code repository:

```bash
# Create external data directory
mkdir ~/dsa4264_data

# Update config.py line 14:
# DATA_DIR = Path.home() / "dsa4264_data"

# Move/copy data files there
mv outputs/* ~/dsa4264_data/
```

### 6. Validate Environment

```bash
python config.py
```

You should see:
```
✅ All required files and directories found!
```

## Usage

### Quick Start: Run Complete Analysis

```bash
jupyter notebook notebooks/multi_school_analysis.ipynb
```

Then execute all cells. The notebook will:
1. Analyze ALL schools and degrees automatically
2. Generate summary comparison tables
3. Create visualizations for representative degrees
4. Save results to `outputs/analysis_results/`

### Configuration

Edit `config.py` to customize:

```python
# Select specific degrees to analyze
DEGREES = {
    "nus": {
        "degrees": {
            "data_sci_analytics": {...},
            # Add/remove degrees here
        }
    }
}

# Adjust analysis parameters
THRESHOLDS = {
    "skill_vote": 0.5,
    "semantic_match": 0.45,
}
```

## Analysis Pipeline

### Phase 1: Global Job Market Analysis (Run Once)

1. **Load Job Embeddings**: Pre-computed MPNet embeddings for 16,000+ jobs
2. **BERTopic Clustering**: Identify job market topics/niches
3. **Hyperparameter Tuning**: Optuna optimization for UMAP + HDBSCAN
4. **Global Visualizations**: Distance maps, hierarchies, topic distributions

**Output**: `outputs/bertopic_visualizations_global/`

### Phase 2: Per-Degree Analysis (Loops Through All)

For each university degree:

1. **Load Module Embeddings**: Pre-computed module descriptions
2. **Approval Voting**: Count modules matching each job (skill-to-skill)
3. **Semantic Similarity**: Average relevance to job descriptions
4. **Market Segmentation**: Kneedle algorithm finds relevant job subset
5. **Module Metrics**:
   - **Relevance (Depth)**: Average similarity to relevant jobs
   - **Breadth**: Number of jobs matched above threshold
   - **Transferability**: Prerequisite connections to other modules

**Output**: `outputs/analysis_results/{school}/{degree}/`

### Phase 3: Cross-Degree Comparison

1. **Summary Statistics**: Job market size, preparation scores, module utilization
2. **Category Analysis**: Compare degrees within same category (e.g., all Data Science degrees)
3. **School-Level Insights**: How universities differ in job market alignment

**Output**: `outputs/summary/comparison_tables.csv`

## Key Metrics Explained

### Job Market Metrics

- **Detected Market Size**: Number of relevant jobs (after Kneedle cutoff)
- **Similarity Cutoff**: Threshold separating relevant from irrelevant jobs
- **Peak Qualification (Union)**: Best single module match per job
- **Collective Relevance (Top-5)**: Average of top 5 module matches per job

### Module Metrics

- **Relevance Score**: Average cosine similarity to all relevant jobs (0-1)
- **Breadth Score**: Count of jobs matched above 60th percentile threshold
- **Transferability Category**:
  - **Highly Transferable**: 20+ prerequisite connections (foundation courses)
  - **Moderately Transferable**: 5-19 connections
  - **Specialized**: 1-4 connections
  - **Terminal/Capstone**: 0 connections (final year projects)

### Preparation Levels

- **Well Prepared**: Jobs where Top-5 module avg > 67th percentile
- **Moderately Prepared**: 33rd-67th percentile
- **Under-prepared**: < 33rd percentile

## Output Files

### Per-Degree Outputs

```
analysis_results/{school}/{degree}/
├── module_analysis_results.csv          # All module metrics
├── relevant_jobs.csv                    # Filtered job market
├── top_100_job_matches.csv              # Best matching jobs
└── visualizations/
    ├── module_breadth_vs_relevance.png
    ├── top_15_relevant_modules.png
    ├── transferability_distribution.png
    └── degree_preparation_distribution.png
```

### Summary Outputs

```
summary/
├── all_degrees_comparison.csv           # Side-by-side metrics
├── category_analysis.csv                # Within-category rankings
├── representative_samples/              # Detailed viz for selected degrees
└── school_level_summary.csv             # University-level insights
```

## Reproducibility

### Deterministic Results

Set random seeds in notebooks:
```python
import random
import numpy as np
np.random.seed(42)
random.seed(42)
```

### Version Lock

Pin exact versions if needed:
```bash
pip freeze > requirements.lock.txt
pip install -r requirements.lock.txt
```

## Data Requirements

### Required Files

| File | Size | Description |
|------|------|-------------|
| `processed_jobs_dual_embeddings.parquet` | ~175MB | Job descriptions with MPNet embeddings |
| `{school}/embeddings/*.parquet` | ~2MB each | Module descriptions with embeddings |
| `mod_importance/*_counts.csv` | <1MB | Prerequisite relationship data |

### Data Schema

**Jobs Parquet:**
- `description` (str): Job description text
- `title` (str): Job title
- `embedding_mpnet` (array): 768-dim MPNet embedding
- `employmentTypes` (list): Employment categories

**Module Parquet:**
- `code` (str): Module code (e.g., DSA4264)
- `title` (str): Module title
- `description` (str): Full module description
- `skill_embedding` (array): 768-dim MPNet embedding
- `course` (str): Degree program name

## Troubleshooting

### Common Issues

**1. Out of Memory Errors**
```python
# In notebook, process in batches:
for degree in degrees[:5]:  # Process 5 at a time
    analyze_degree(degree)
```

**2. Missing Data Files**
```bash
# Check which files are missing:
python config.py

# Expected output shows missing files
```

**3. Slow Performance**
```python
# Reduce BERTopic trials in config.py:
BERTOPIC_TRIALS = 3  # Down from 10
```

**4. ModuleNotFoundError**
```bash
# Ensure virtual environment is activated:
source .venv/bin/activate

# Reinstall dependencies:
pip install -r requirements.txt
```

## Citation

If you use this work, please cite:

```bibtex
@misc{dsa4264_analysis,
  title={University Degree to Job Market Analysis},
  author={Your Name},
  year={2024},
  institution={National University of Singapore}
}
```

## License

This project is for academic use only. Data sources:
- Job postings: [Your data source]
- Module descriptions: NUSMods API, university handbooks

## Contact

For questions or issues:
- Create an issue on GitHub
- Email: your.email@example.com

## Acknowledgments

- **NUSMods API** for module data
- **Sentence Transformers** for embedding models
- **BERTopic** for topic modeling framework
