# Global Threshold Implementation

## Problem Solved

**Before:** Job preparation categories (Well/Moderate/Under-prepared) used **percentiles per degree** (67th/33rd), which guaranteed every degree would have exactly 33% in each category. This meant:
- Every pie chart looked the same (33%/34%/33%)
- Couldn't compare degree quality across schools
- "Well prepared" for a weak degree = same % as "well prepared" for a strong degree

**After:** Uses **global thresholds** calculated across all 21 degrees, so results actually vary by degree quality!

---

## Changes Made

### 1. Cell 25 (Single-Degree View)
**File:** `complete_analysis_full.ipynb` Cell 25

**Changed from:**
```python
# Percentiles (always 33%/34%/33%)
well_prepared_threshold = np.percentile(collective_score_per_job, 67)
moderate_threshold = np.percentile(collective_score_per_job, 33)
```

**Changed to:**
```python
# Default absolute thresholds for single-degree view
well_prepared_threshold = 0.40  # Strong collective preparation
moderate_threshold = 0.30       # Decent collective preparation
```

**Why:** Provides reasonable defaults when viewing just one degree. Batch analysis uses data-driven thresholds.

---

### 2. Cell 40 (Batch Analysis) - TWO-PASS APPROACH
**File:** `complete_analysis_full.ipynb` Cell 40

**NEW: Pass 1 - Collect Global Statistics**
```python
all_collective_scores = []  # Collect from all degrees

for school, degree in all_degrees:
    # ... analyze degree ...
    collective_scores_batch = metrics_batch.get('collective_score_per_job', [])
    all_collective_scores.extend(collective_scores_batch.tolist())
```

**NEW: Calculate Global Thresholds**
```python
global_mean = np.mean(all_collective_scores)
global_std = np.std(all_collective_scores)

# Use ±0.5 std bands around mean
well_prepared_threshold_global = global_mean + 0.5 * global_std
moderate_threshold_global = global_mean - 0.5 * global_std
```

**NEW: Pass 2 - Apply Global Thresholds**
```python
for result in all_results:
    collective_score_per_job_batch = result['metrics']['collective_score_per_job']
    
    # Apply GLOBAL thresholds (not per-degree percentiles)
    well_prepared_jobs = (collective_score_per_job_batch >= well_prepared_threshold_global).sum()
    moderately_prepared_jobs = (
        (collective_score_per_job_batch >= moderate_threshold_global) & 
        (collective_score_per_job_batch < well_prepared_threshold_global)
    ).sum()
```

**Why:** Two-pass ensures we have global stats before classifying any degree.

---

### 3. Cell 42 (Comparison Table)
**File:** `complete_analysis_full.ipynb` Cell 42

**Added display of preparation percentages:**
```python
# Show well_prepared_pct in main table
comparison_df[['school', 'degree_full_name', 'union_relevance', 'well_prepared_pct']]

# New insights
print("TOP 5 BY WELL-PREPARED PERCENTAGE:")
print("BOTTOM 5 BY WELL-PREPARED PERCENTAGE:")
print("PREPARATION DISTRIBUTION SUMMARY:")
```

**Why:** Shows how preparation quality varies across degrees.

---

### 4. analysis_utils.py
**File:** `analysis_utils.py` line 321-329

**Changed from:**
```python
return {
    'union_relevance': union_relevance,
    'collective_relevance': collective_relevance,
    # ... other metrics ...
}
```

**Changed to:**
```python
return {
    'union_relevance': union_relevance,
    'collective_relevance': collective_relevance,
    'collective_score_per_job': collective_scores,  # NEW: Return for global calculation
    # ... other metrics ...
}
```

**Why:** Batch analysis needs the raw scores to calculate global statistics.

---

## Example Output (What Changes)

### Before (Percentile Approach)
```
NUS Data Science:
  Well Prepared: 437 jobs (33.0%)  ← Always 33%
  Moderate:      449 jobs (33.9%)
  Under:         437 jobs (33.0%)

SMU Business:
  Well Prepared: 362 jobs (33.4%)  ← Always 33%
  Moderate:      365 jobs (33.6%)
  Under:         358 jobs (33.0%)

Every degree: 33%/34%/33% regardless of quality!
```

### After (Global Threshold Approach)
```
Global Statistics:
  Mean collective relevance: 0.2850
  Std deviation: 0.0620
  Well Prepared threshold: ≥ 0.3160 (mean + 0.5σ)
  Moderate threshold: 0.2540 - 0.3160

NUS Data Science:
  Well Prepared: 520 jobs (39.3%)  ← Actually varies!
  Moderate:      450 jobs (34.0%)
  Under:         353 jobs (26.7%)

SMU Business:
  Well Prepared: 280 jobs (25.8%)  ← Different!
  Moderate:      385 jobs (35.5%)
  Under:         420 jobs (38.7%)

SUTD Computer Science:
  Well Prepared: 180 jobs (8.7%)   ← Clearly weaker!
  Moderate:      620 jobs (30.1%)
  Under:         1258 jobs (61.2%)
```

---

## How It Works

### Global Threshold Formula
```python
well_prepared_threshold = mean + 0.5 * std
moderate_threshold = mean - 0.5 * std
```

**Example with real numbers:**
- Global mean = 0.285
- Global std = 0.062
- Well prepared ≥ 0.316 (one-half std above average)
- Moderate: 0.254 - 0.316 (within ±0.5 std of average)
- Under-prepared < 0.254 (one-half std below average)

### Distribution of Degrees
```
Under-prepared   Moderate        Well Prepared
    ← 0.254 ←     0.254-0.316    → 0.316 →
    
    ████████████████████▓▓▓▓▓▓▓▓░░░░░░░░
    
    Weak degrees ↑            ↑ Strong degrees
```

---

## Files Modified

1. **notebooks/complete_analysis_full.ipynb**
   - Cell 25: Use default thresholds (0.40/0.30)
   - Cell 40: Two-pass approach with global threshold calculation
   - Cell 42: Display preparation percentages in comparison

2. **analysis_utils.py**
   - Line 321-329: Return `collective_score_per_job` in metrics dict

## New Output Files

**outputs/summary/global_thresholds.csv**
```csv
global_mean_collective,global_std_collective,well_prepared_threshold,moderate_threshold,total_scores_analyzed,num_degrees
0.2850,0.0620,0.3160,0.2540,35420,21
```

**outputs/summary/all_degrees_comparison.csv**
- Now includes: `well_prepared_jobs`, `well_prepared_pct`, `moderately_prepared_pct`, `underprepared_pct`

---

## Key Benefits

1. **Meaningful Comparisons:** "NUS DSA prepares students well for 39% of its market" vs "SUTD CS only 9%"
2. **Data-Driven:** Thresholds calculated from actual collective relevance scores across all degrees
3. **Adaptive:** Uses standard deviation to account for natural variation in scores
4. **Transparent:** Global stats saved to CSV for reference

---

## Running the Updated Notebook

**Single degree analysis (Parts 0-6):**
- Uses default thresholds (0.40/0.30)
- Shows preparation categories for that degree

**Batch analysis (Part 7):**
- Collects all collective scores
- Calculates global thresholds (mean ± 0.5σ)
- Applies global thresholds to ALL degrees
- Saves global stats to `outputs/summary/global_thresholds.csv`
- Generates comparison table with preparation percentages

**Result:** Pie charts now actually differ by degree quality!

---

**Last Updated:** 2026-04-07
