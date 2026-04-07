# Hybrid Analysis: Prerequisite Scaffolding + Job Alignment

## Overview

This **extension layer** combines two dimensions to understand how job-relevant capabilities are structured in the curriculum:

1. **Job Alignment** (already in base analysis): How relevant is this module to the job market?
2. **Prerequisite Centrality** (NEW): How structurally important is this module in the curriculum?

## Key Insight

Instead of saying:
> "Prerequisite analysis measures employability"

We say:
> **"Prerequisite structure helps explain whether job-relevant capabilities are deeply scaffolded across the curriculum or concentrated in a few standalone modules."**

This is much more rigorous and interpretable.

---

## The 2×2 Classification

### 1. High Alignment + High Centrality
**"Core Market-Ready Foundations"**

- Strongest modules
- Both job-relevant AND deeply embedded in curriculum
- Examples: Core programming, statistics, data structures

**Interpretation**: These modules are the **backbone** of job preparation. They're prerequisites for many other modules AND highly valued by employers.

### 2. High Alignment + Low Centrality
**"Specialized Market Skills"**

- Valuable but possibly isolated
- Often electives, advanced topics, or specialized modules
- Examples: Machine learning, blockchain, advanced analytics

**Interpretation**: These provide **direct job value** but aren't deeply scaffolded. Students can pick them up later, but they're immediately applicable.

### 3. Low Alignment + High Centrality
**"Foundational Prerequisites"**

- Structurally important but more indirect
- Math, statistics, programming basics
- Examples: Calculus, linear algebra, intro programming

**Interpretation**: These are **enablers** - not directly mentioned in job postings, but essential foundations for everything else.

### 4. Low Alignment + Low Centrality
**"Peripheral Modules"**

- Less influential in both dimensions
- May be breadth requirements, general education, or niche topics
- Examples: Liberal arts electives, specialized theory courses

**Interpretation**: These have **limited direct impact** on both curriculum structure and job outcomes, but may serve other educational goals.

---

## Usage in Notebook

### Step 1: Load Config
```python
import sys
sys.path.append('..')
import config
from analysis_utils import *
```

### Step 2: Run Base Analysis (as usual)
```python
# Load modules, calculate similarities, filter jobs
modules_df = load_degree_modules(school, degree, config)
# ... existing analysis ...
module_analysis_df = analyze_modules(...)
```

### Step 3: Add Hybrid Analysis (NEW)
```python
# Get prerequisite data path
prereq_path = config.PREREQ_DATA_DIR / f"{degree}_counts.csv"
degree_output_dir = config.get_degree_output_dir(school, degree)

# Run hybrid analysis
module_analysis_df = run_hybrid_analysis(
    module_analysis_df,
    prereq_path,
    degree_output_dir,
    config
)
```

### Step 4: Interpret Results
```python
# Check distribution
print(module_analysis_df['hybrid_bucket_name'].value_counts())

# Identify strongest modules
core_foundations = module_analysis_df[
    module_analysis_df['hybrid_bucket'] == 'high_align_high_central'
].sort_values('relevance_score', ascending=False)

print("Strongest modules (job-relevant AND structurally central):")
print(core_foundations[['module_code', 'relevance_score', 'centrality_score']].head(10))
```

---

## Outputs Generated

### 1. CSV: `hybrid_scaffolding_summary.csv`
Contains:
- Scaffolding type (Deeply Scaffolded / Concentrated / Foundation-Heavy / Balanced)
- Interpretation text
- Count and percentage in each bucket
- Full distribution

### 2. PNG: `hybrid_analysis_2x2.png`
Scatter plot showing:
- X-axis: Job alignment score
- Y-axis: Prerequisite centrality
- Color-coded by bucket
- Threshold lines showing classification boundaries
- Top modules labeled

### 3. Updated: `module_analysis_results.csv`
Now includes additional columns:
- `direct_dependents`: How many modules require this as prerequisite
- `transitive_dependents`: Transitive closure (if available)
- `centrality_score`: Combined centrality metric
- `hybrid_bucket`: Classification bucket
- `hybrid_bucket_name`: Human-readable name

---

## Configuration

In `config.py`:

```python
HYBRID_ANALYSIS = {
    "enabled": True,  # Toggle on/off
    "alignment_threshold_high": 0.25,  # What counts as "high alignment"
    "centrality_threshold_high": 10,   # What counts as "high centrality"
    "include_transitive": True,        # Use transitive closure
}
```

### Tuning Thresholds

**For specialized degrees** (e.g., Data Science):
```python
"alignment_threshold_high": 0.30,  # Stricter - fewer high-aligned modules
"centrality_threshold_high": 15,   # Stricter - only truly foundational modules
```

**For broad degrees** (e.g., Business):
```python
"alignment_threshold_high": 0.20,  # Looser - more modules count as aligned
"centrality_threshold_high": 5,    # Looser - more modules are "central"
```

---

## Integration with Existing Analysis

This is an **extension layer**, so it doesn't replace anything:

### Base Analysis (Always Runs)
- **Layer 1**: Market alignment (relevance, breadth)
- **Layer 2**: Reach and coverage
- **Layer 3**: Robustness across curriculum

### Hybrid Analysis (Optional Extension)
- **Layer 4**: Prerequisite scaffolding interpretation
  - How are job-relevant capabilities structured?
  - Are they deeply scaffolded or concentrated?
  - Which modules are structurally vs. directly valuable?

---

## Example Insights

### Deeply Scaffolded Curriculum
```
NUS Data Science & Analytics:
- 35% Core Market-Ready Foundations
- Programming, Stats, ML form prerequisite chains
- Job-relevant skills progressively built through 3+ semesters
```

**Interpretation**: Students develop job-ready skills gradually through interconnected modules.

### Concentrated Curriculum
```
SMU Business Analytics:
- 40% Specialized Market Skills (low centrality)
- Advanced analytics courses are standalone electives
- Few prerequisite chains leading to job-relevant modules
```

**Interpretation**: Job-relevant skills are available but not deeply integrated into core curriculum structure.

### Foundation-Heavy Curriculum
```
NUS Engineering (General):
- 45% Foundational Prerequisites (low direct alignment)
- Strong math/physics foundations
- But fewer modules with direct job market alignment
```

**Interpretation**: Strong structural foundations, but indirect connection to specific job outcomes. Students build transferable fundamentals.

---

## Report Structure Recommendation

When writing your final report, organize like this:

### Main Analysis
1. **Market Alignment**: Which modules are most relevant to jobs?
2. **Reach & Breadth**: How many jobs can graduates access?
3. **Robustness**: How well does the degree cover the job market?

### Extension (Hybrid Analysis)
4. **Prerequisite Scaffolding**: How are job-relevant capabilities structured?
   - Classification of modules into 4 buckets
   - Scaffolding type (Deeply Scaffolded / Concentrated / etc.)
   - Implications for curriculum design

This way it **supports your main story** without distracting from it.

---

## Advantages of This Approach

✅ **More Rigorous**: Doesn't claim prerequisites = employability directly
✅ **Interpretable**: Clear buckets with meaningful distinctions
✅ **Actionable**: Curriculum designers can identify gaps
✅ **Comparative**: Can compare scaffolding approaches across universities
✅ **Non-Distracting**: Optional layer that enhances without complicating

---

## Comparison: Your Approach vs Friend's Approach

| Dimension | Your Original | Friend's Approach | Hybrid (Combined) |
|-----------|---------------|-------------------|-------------------|
| **Scope** | Degree-specific job market | Entire job market | Both (configurable) |
| **Prerequisite Use** | Transferability categories | Central vs Isolated | 4-bucket classification |
| **Key Metric** | Relevance + Breadth | Alignment + Centrality | Both integrated |
| **Interpretation** | "Which modules matter?" | "How are skills structured?" | Both questions answered |

**Your hybrid approach is stronger** because it answers both:
1. What job-relevant skills does the degree teach? (Your analysis)
2. How are those skills scaffolded in the curriculum? (Friend's insight)

---

## Future Extensions

If you have more time:

### 1. Transitive Dependency Graph
Build actual prerequisite graph and calculate:
- PageRank centrality
- Betweenness centrality
- Shortest paths from foundations to job-relevant modules

### 2. Compare Across Universities
Which schools scaffold job-relevant skills more deeply?

### 3. Temporal Analysis
Do modules become more/less central over time as curriculum changes?

---

## Quick Checklist

Before running hybrid analysis:

- [x] Prerequisite data available for degree?
- [x] Base analysis (relevance scores) computed?
- [x] Thresholds configured appropriately?
- [x] `HYBRID_ANALYSIS['enabled'] = True` in config?

If all ✓, then:
```python
module_analysis_df = run_hybrid_analysis(
    module_analysis_df, prereq_path, output_dir, config
)
```

That's it! The function handles everything else.
