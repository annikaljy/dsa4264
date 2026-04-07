# Degree-to-Job Market Alignment Analysis

## Overview

This project analyzes how well university degree programs prepare students for the job market by measuring the semantic alignment between course modules and job descriptions using MPNet embeddings.

### Core Question
**How well does each degree program's curriculum prepare students for their own filtered job market?**

## Key Analysis Concepts

### 1. Degree-Specific Job Market Filtering

Instead of comparing all degrees against the entire job market, we:
- Calculate each degree's semantic similarity to all jobs
- Use **Kneedle algorithm** to automatically identify the relevant job market for that specific degree
- Analyze how well the degree prepares students for **its own** filtered market

**Why this matters:** A biomedical engineering degree shouldn't be judged by how well it prepares students for software jobs. Each degree has its own target market.

### 2. Semantic Similarity Metrics

**MPNet Embeddings (768-dimensional vectors)**
- Each course module description → embedded vector
- Each job description → embedded vector
- Similarity measured using cosine similarity

**Approval Voting (threshold = 0.5)**
- A module "votes" for a job if similarity ≥ 0.5
- Counts how many modules find each job relevant
- Identifies which jobs align with the degree's skillset

### 3. Relevance Scoring

**Union Relevance**
- Best single-module match to each job
- Measures: "What's the strongest skill we teach for each job?"
- Formula: `max(similarity across all modules) per job`

**Collective Relevance (Top-5 Coverage)**
- Average of top 5 module matches per job
- Measures: "How comprehensively do our top skills cover each job?"
- Formula: `mean(top 5 similarities) per job`

**Module-Level Metrics**
- **Semantic match**: Average similarity to all relevant jobs
- **Breadth**: Percentage of jobs this module is relevant to (percentile-based)
- **Relevance score**: `(semantic_match + breadth) / 2`

### 4. Job Market Preparation Categories

Based on collective relevance scores, jobs are classified into:

1. **Well Prepared** (top 33% of collective scores)
   - Degree provides comprehensive skillset coverage
   - Multiple modules align strongly with job requirements

2. **Moderately Prepared** (middle 34%)
   - Partial skill alignment
   - Some gaps in curriculum coverage

3. **Under Prepared** (bottom 33%)
   - Limited skill overlap
   - Significant curriculum gaps for these roles

### 5. Module Utilization Analysis

**Active Core Modules**
- High relevance + High breadth
- The "workhorses" of job market preparation
- Formula: Modules in top 60th percentile for both metrics

**Supporting Skill Modules**
- Moderate relevance or breadth
- Specialized or niche skills
- Formula: Modules not in active core but still relevant

**Utilization Percentages**
- `Active Core Utilization = (# active core modules / total modules) × 100`
- `Supporting Skill Breadth = (# supporting modules / total modules) × 100`

### 6. BERTopic Clustering

**Purpose:** Discover latent job market themes automatically

**Method:**
- UMAP dimensionality reduction (2D projection)
- HDBSCAN clustering
- c-TF-IDF for topic representation
- Optuna hyperparameter tuning (10 trials)

**Output:** Identifies major job categories and their characteristics within the filtered market

### 7. Hybrid Analysis (NUS only)

**Combines job alignment with curriculum structure analysis**

For degrees with prerequisite data:
- **Centrality Score**: Number of modules that depend on this module
- **Alignment Score**: Job market relevance

**Module Classification:**
1. **Core Market-Ready Foundations**
   - High alignment + High centrality
   - Both job-relevant AND foundational to curriculum

2. **Specialized Market Skills**
   - High alignment + Low centrality
   - Job-relevant but isolated (electives, advanced topics)

3. **Foundational Prerequisites**
   - Low alignment + High centrality
   - Structurally important (math, stats) but indirect job relevance

4. **Peripheral Modules**
   - Low alignment + Low centrality
   - Less influential in both dimensions

## Technical Implementation

### Data Sources

**Job Market Data**
- File: `processed_jobs_dual_embeddings.parquet`
- Contains: Job descriptions, titles, employment types, MPNet embeddings
- Filter: Full-time, permanent, contract positions only

**Module Data**
- School-specific embeddings directories
- NUS: 10 degrees (data science, business analytics, engineering, etc.)
- SMU: 6 degrees (business, accountancy, information systems, etc.)
- SUTD: 5 degrees (computer science, engineering, design, etc.)
- Total: 21 degree programs

### Analysis Pipeline

```
1. Load degree modules + embeddings
2. Load job market data + embeddings
3. Calculate similarity matrix (modules × jobs)
4. Apply approval voting (threshold 0.5)
5. Find relevant job market using Kneedle algorithm
6. Analyze module-level metrics
7. Calculate degree-level metrics
8. Classify job preparation categories
9. Run BERTopic clustering
10. Generate visualizations
11. Save results
```

### Kneedle Algorithm Details

**Purpose:** Automatically find cutoff threshold for relevant jobs

**How it works:**
1. Sort jobs by average semantic similarity (descending)
2. Smooth the curve to reduce noise (dynamic window size)
3. Calculate auto-sensitivity (S) based on curve shape
4. Apply Kneedle to detect "elbow" in sorted curve
5. Use cutoff score (not rank) to filter jobs

**Auto-S Logic (The Smart Part):**

The algorithm automatically adjusts its sensitivity based on each degree's curve:

```python
# Measure curve steepness
diffs = abs(differences between consecutive scores)
avg_drop = mean(diffs)      # How fast similarity drops on average
std_drop = std_dev(diffs)   # How consistently it drops

# Calculate adaptive sensitivity
S = 1.0 + (avg_drop / std_drop)
```

**What this means:**
- **Specialized degree** (e.g., Biomedical Engineering): Curve has sharp drop with consistent pattern → High `avg_drop/std_drop` ratio → **High S** → Finds clear elbow easily
- **General degree** (e.g., Business): Curve is smooth gradual slide → Low `avg_drop/std_drop` ratio → **Lower S** → More conservative, avoids false elbows

**Visual Example:**

```
Specialized Degree Curve:          General Degree Curve:
0.40 |███████\                     0.30 |████████\
0.35 |        \___                 0.25 |          \_
0.30 |            \                0.20 |            \_
0.25 |             \_              0.15 |              \_
0.20 |               \_____        0.10 |                \____
       ↑ Sharp elbow (S=2.5)              ↑ Gentle elbow (S=1.2)
```

**Result:** Each degree gets its own optimized sensitivity - no manual tuning needed!

**Tie-breaking:** Keep ALL jobs with score ≥ cutoff (score-based, not rank-based)

**Example Output:**
```
Smoothing window: 33 jobs
Calculated Curve Sensitivity (S): 1.87
Kneedle found elbow at rank 1251
Market Size: 1,260 jobs (with cutoff = 0.1689)
Jobs at cutoff score: 10 (all kept)
```

## Output Structure

```
outputs/
├── analysis_results/
│   ├── {school}/
│   │   ├── {degree}/
│   │   │   ├── visualizations/
│   │   │   │   ├── module_breadth_vs_relevance.png
│   │   │   │   ├── top_modules_barchart.png
│   │   │   │   ├── union_collective_comparison.png
│   │   │   │   ├── collective_scores_distribution.png
│   │   │   │   ├── job_preparation_coverage.png
│   │   │   │   ├── module_utilization_breakdown.png
│   │   │   │   ├── topic_clusters_umap.png
│   │   │   │   └── topic_distribution_piechart.png
│   │   │   ├── module_analysis.csv
│   │   │   ├── relevant_jobs.csv
│   │   │   └── degree_summary.json
└── summary/
    └── all_degrees_comparison.csv
```

## Key Metrics Summary

### Degree-Level Metrics
- **Market Size**: Number of relevant jobs identified by Kneedle
- **Market Cutoff Score**: Similarity threshold used for filtering
- **Union Relevance**: Average of best module matches across jobs
- **Collective Relevance**: Average of top-5 module coverage across jobs
- **Active Core Utilization %**: Percentage of modules that are high-performing
- **Supporting Skill Breadth %**: Percentage of specialized/supporting modules
- **Well Prepared Jobs**: Number of jobs the degree prepares students well for
- **Well Prepared %**: Percentage of market with comprehensive preparation

### Module-Level Metrics
- **Semantic Match**: Average similarity to relevant jobs
- **Breadth**: Job market coverage (percentile-based)
- **Relevance Score**: Combined metric (average of semantic + breadth)
- **Centrality Score**: Prerequisite importance (NUS only)
- **Hybrid Bucket**: Classification based on alignment × centrality

## Workflow for Prof Saif

**Single Notebook:** `complete_analysis_full.ipynb`

**Part 0-6:** Detailed analysis of NUS Data Science & Analytics
- Generates all 8 visualizations
- Shows detailed metrics and insights
- Example walkthrough of the methodology

**Part 7:** Batch analysis of all 21 degrees
- Reuses loaded job data for efficiency
- Processes all schools and degrees
- Generates comparison table: `all_degrees_comparison.csv`

**Runtime:** ~30-45 minutes for complete analysis

## Insights Enabled

1. **Which degrees are best aligned with their target markets?**
   - Compare union and collective relevance across degrees

2. **Are we efficiently using our curriculum?**
   - Active core utilization shows if modules are pulling their weight

3. **Where are the gaps?**
   - Under-prepared job categories reveal curriculum blind spots

4. **What are the major job market themes?**
   - BERTopic clusters reveal industry structure

5. **Are foundational courses job-relevant?**
   - Hybrid analysis (NUS) shows prerequisite vs market alignment

## Configuration

All settings centralized in `config.py`:
- File paths (data, outputs)
- Degree definitions (21 degrees across 3 schools)
- Thresholds (approval voting, semantic matching, breadth percentiles)
- BERTopic parameters (10 Optuna trials)
- Visualization settings
- Hybrid analysis toggles

## Dependencies

- `pandas`, `numpy`: Data manipulation
- `sentence-transformers`: MPNet embeddings (already computed)
- `scikit-learn`: Cosine similarity, metrics
- `kneed`: Kneedle algorithm for automatic thresholding
- `bertopic`: Topic modeling with Optuna optimization
- `matplotlib`, `seaborn`: Visualizations
- `tqdm`: Progress tracking

---

**Last Updated:** April 2026
