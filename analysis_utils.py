"""
Utility functions for degree-to-job market analysis
===================================================
Reusable functions for module analysis, job filtering, and metric calculation.
"""

import numpy as np
import pandas as pd
import requests
import time
from sklearn.metrics.pairwise import cosine_similarity
from kneed import KneeLocator


# ============================================
# NUSMODS API FUNCTIONS
# ============================================

def fetch_nusmods_module(module_code, year=2025):
    """
    Fetch module data from NUSMods API for specific academic year.

    Args:
        module_code: Module code (e.g., 'DSA4264')
        year: Academic year (default 2025 for AY2025-2026)

    Returns:
        dict with module data or None if not found
    """
    url = f"https://api.nusmods.com/v2/{year}-{year+1}/modules/{module_code.upper()}.json"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return {
                "code": module_code,
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "faculty": data.get("faculty", ""),
                "department": data.get("department", ""),
                "academic_year": f"{year}-{year+1}",
                "moduleCredit": data.get("moduleCredit", ""),
                "workload": data.get("workload", "")
            }
    except requests.RequestException:
        pass

    return None


def fetch_modules_batch(module_codes, config, progress_interval=20):
    """
    Fetch module descriptions from NUSMods API (AY2025-2026 only).
    Modules without descriptions will be dropped.

    Args:
        module_codes: List of module codes
        config: Config module with START_YEAR
        progress_interval: Print progress every N modules

    Returns:
        DataFrame with successfully fetched modules (with descriptions)
    """
    print(f"Fetching {len(module_codes)} modules from NUSMods API...")
    print(f"Academic Year: {config.START_YEAR}-{config.START_YEAR + 1}")

    results = []
    missing = []

    for i, code in enumerate(module_codes):
        if i > 0 and i % progress_interval == 0:
            print(f"  Progress: {i}/{len(module_codes)} modules...")

        data = fetch_nusmods_module(code, year=config.START_YEAR)

        # Only keep if we got data AND description is not empty
        if data and data.get('description', '').strip():
            results.append(data)
        else:
            missing.append(code)

        # Rate limiting
        time.sleep(0.1)

    print(f"\n✓ Fetched with descriptions: {len(results)} modules")

    if missing:
        print(f"✗ Dropped (not found or no description): {len(missing)} modules")
        if len(missing) <= 10:
            print(f"   {', '.join(missing)}")
        else:
            print(f"   Examples: {', '.join(missing[:10])}")

    return pd.DataFrame(results)


def load_degree_modules(school, degree, config):
    """Load module embeddings for a specific degree."""
    embeddings_path = config.get_degree_embeddings_path(school, degree)

    if not embeddings_path.exists():
        raise FileNotFoundError(f"Embeddings not found: {embeddings_path}")

    df = pd.read_parquet(embeddings_path)
    return df


def extract_embeddings(df, embedding_column='embedding_mpnet'):
    """
    Extract embedding vectors from DataFrame into a numpy array.

    Args:
        df: DataFrame with embedding column
        embedding_column: Name of column containing embeddings

    Returns:
        numpy array of shape (n_samples, embedding_dim)
    """
    if embedding_column not in df.columns:
        raise ValueError(f"Column '{embedding_column}' not found. Available: {df.columns.tolist()}")

    return np.stack(df[embedding_column].values)


def filter_jobs_by_employment_type(jobs_df, allowed_types=None):
    """Filter jobs to only include specified employment types."""
    if allowed_types is None:
        allowed_types = {"Full Time", "Permanent", "Contract"}

    def keeps_allowed_types(emp_types):
        try:
            return bool(set(emp_types) & allowed_types)
        except TypeError:
            return False

    return jobs_df[jobs_df['employmentTypes'].apply(keeps_allowed_types)].copy()


def calculate_approval_voting(module_embeddings, job_embeddings, threshold=0.5):
    """
    Calculate approval voting scores for jobs based on module similarity.

    Returns:
        similarity_matrix: Module x Job similarity matrix
        votes_per_job: Number of modules "voting" for each job
        avg_similarity: Average similarity per job
    """
    similarity_matrix = cosine_similarity(module_embeddings, job_embeddings)

    votes_matrix = similarity_matrix >= threshold
    votes_per_job = votes_matrix.sum(axis=0)
    avg_similarity = similarity_matrix.mean(axis=0)

    return similarity_matrix, votes_per_job, avg_similarity


def find_relevant_job_market(jobs_df, similarities, method='kneedle'):
    """
    Find the relevant job market using Kneedle algorithm or percentile cutoff.

    Args:
        jobs_df: DataFrame of all jobs
        similarities: Array of similarity scores (must match jobs_df order)
        method: 'kneedle' or 'percentile'

    Returns:
        relevant_jobs_df: Filtered DataFrame of relevant jobs
        cutoff_index: Index where cutoff was applied
        cutoff_score: Similarity score at cutoff
    """
    # Sort jobs by similarity
    jobs_sorted = jobs_df.copy()
    jobs_sorted['_similarity'] = similarities
    jobs_sorted = jobs_sorted.sort_values('_similarity', ascending=False).reset_index(drop=True)
    sorted_similarities = jobs_sorted['_similarity'].values

    if method == 'kneedle':
        # Dynamic smoothing window
        window = max(10, len(sorted_similarities) // 500)
        smooth_series = pd.Series(sorted_similarities).rolling(window=window, center=True).mean()
        smooth_scores = smooth_series.dropna().values

        # Auto-calculate sensitivity
        diffs = np.abs(np.diff(smooth_scores))
        avg_drop = np.mean(diffs)
        std_drop = np.std(diffs)
        auto_s = 1.0 + (avg_drop / (std_drop + 1e-9))
        auto_s = np.clip(auto_s, 0.5, 5.0)

        # Apply Kneedle
        kn = KneeLocator(
            range(len(smooth_scores)),
            smooth_scores,
            curve='convex',
            direction='decreasing',
            S=auto_s
        )

        if kn.knee:
            cutoff_idx = kn.knee + (window // 2)
        else:
            # Fallback: dynamic noise floor
            score_range = sorted_similarities.max() - sorted_similarities.min()
            dynamic_floor = sorted_similarities.min() + (score_range * 0.20)
            noise_indices = np.where(sorted_similarities < dynamic_floor)[0]
            cutoff_idx = noise_indices[0] if len(noise_indices) > 0 else len(sorted_similarities) // 10

    elif method == 'percentile':
        # Use 75th percentile as cutoff
        cutoff_score = np.percentile(sorted_similarities, 25)  # Top 75%
        cutoff_idx = np.where(sorted_similarities >= cutoff_score)[0][-1]

    else:
        raise ValueError(f"Unknown method: {method}")

    # Get cutoff score and filter by score (not rank) to handle ties correctly
    cutoff_score = sorted_similarities[cutoff_idx]
    relevant_jobs = jobs_sorted[jobs_sorted['_similarity'] >= cutoff_score].copy()

    # Remove temp column
    relevant_jobs = relevant_jobs.drop(columns=['_similarity'])

    return relevant_jobs, cutoff_idx, cutoff_score


def analyze_modules(modules_df, relevant_jobs_df, similarity_matrix, breadth_percentile=60):
    """
    Analyze module relevance, breadth, and transferability.

    Args:
        modules_df: DataFrame of modules with embeddings
        relevant_jobs_df: DataFrame of relevant jobs
        similarity_matrix: Full module x job similarity matrix
        breadth_percentile: Percentile threshold for breadth calculation

    Returns:
        DataFrame with module analysis metrics
    """
    # Extract relevant portion of similarity matrix
    relevant_indices = relevant_jobs_df.index
    relevant_sim_matrix = similarity_matrix[:, relevant_indices]

    # Calculate breadth threshold
    match_threshold = np.percentile(relevant_sim_matrix.flatten(), breadth_percentile)

    module_results = []
    for i, (idx, module) in enumerate(modules_df.iterrows()):
        module_sims = relevant_sim_matrix[i]

        # Relevance (Depth): average similarity to relevant jobs
        relevance_score = np.mean(module_sims)

        # Breadth: number of jobs matched above threshold
        breadth_score = (module_sims > match_threshold).sum()

        # Max similarity
        max_similarity = np.max(module_sims)

        # Get module title (may not exist in some datasets)
        module_title = module.get('title', module.get('description', '')[:50] if pd.notna(module.get('description')) else '')

        module_results.append({
            'module_code': module.get('code', ''),
            'module_title': module_title,
            'module_type': module.get('type', ''),
            'relevance_score': relevance_score,
            'breadth_score': breadth_score,
            'max_similarity': max_similarity,
            'num_matching_jobs': breadth_score
        })

    return pd.DataFrame(module_results)


def calculate_degree_metrics(modules_df, relevant_jobs_df, similarity_matrix):
    """
    Calculate overall degree-level metrics.

    Returns:
        dict with metrics:
        - market_size: Number of relevant jobs
        - union_relevance: Best single module match per job (mean)
        - collective_relevance: Average of top-5 module matches per job
        - active_utilization: % of modules actively used
        - niche_utilization: % of modules providing niche value
    """
    relevant_indices = relevant_jobs_df.index
    market_sim_matrix = similarity_matrix[:, relevant_indices]

    # Union-based (best single module)
    max_sims_per_job = np.max(market_sim_matrix, axis=0)
    union_relevance = np.mean(max_sims_per_job)

    # Collective (top-5 modules)
    top_k = min(5, len(modules_df))
    top_k_indices = np.argsort(market_sim_matrix, axis=0)[-top_k:, :]
    top_k_scores = np.take_along_axis(market_sim_matrix, top_k_indices, axis=0)
    collective_scores = np.mean(top_k_scores, axis=0)
    collective_relevance = np.mean(collective_scores)

    # Active utilization
    unique_elements, counts = np.unique(top_k_indices, return_counts=True)
    module_contribution = np.zeros(len(modules_df))
    module_contribution[unique_elements] = counts

    active_threshold = max(1, len(relevant_jobs_df) * 0.01)
    active_modules = (module_contribution >= active_threshold).sum()
    active_utilization = (active_modules / len(modules_df)) * 100

    # Niche utilization
    useful_modules = ((market_sim_matrix >= 0.30).sum(axis=1) >= active_threshold).sum()
    niche_utilization = (useful_modules / len(modules_df)) * 100

    # Job preparation levels
    well_prepared_threshold = np.percentile(collective_scores, 67)
    well_prepared_count = (collective_scores >= well_prepared_threshold).sum()
    well_prepared_pct = (well_prepared_count / len(relevant_jobs_df)) * 100

    return {
        'market_size': len(relevant_jobs_df),
        'union_relevance': union_relevance,
        'collective_relevance': collective_relevance,
        'collective_score_per_job': collective_scores,  # NEW: Return for global threshold calculation
        'active_utilization': active_utilization,
        'niche_utilization': niche_utilization,
        'well_prepared_jobs': well_prepared_count,
        'well_prepared_pct': well_prepared_pct
    }


def add_transferability_analysis(module_analysis_df, prereq_csv_path):
    """
    Add transferability metrics based on prerequisite relationships.

    Args:
        module_analysis_df: DataFrame with module analysis
        prereq_csv_path: Path to prerequisite counts CSV

    Returns:
        DataFrame with added transferability columns
    """
    if not prereq_csv_path.exists():
        # No prerequisite data available
        module_analysis_df['transferability_category'] = 'Unknown'
        return module_analysis_df

    prereq_df = pd.read_csv(prereq_csv_path)

    # Merge with module analysis
    result_df = module_analysis_df.merge(
        prereq_df[['module', 'level_1', 'level_2', 'level_3', 'level_4', 'total']],
        left_on='module_code',
        right_on='module',
        how='left'
    )

    # Fill NaN with 0
    for col in ['level_1', 'level_2', 'level_3', 'level_4', 'total']:
        if col not in result_df.columns:
            result_df[col] = 0
        else:
            result_df[col] = result_df[col].fillna(0)

    # Categorize
    result_df['transferability_category'] = 'Specialized'
    result_df.loc[result_df['total'] >= 20, 'transferability_category'] = 'Highly Transferable'
    result_df.loc[(result_df['total'] >= 5) & (result_df['total'] < 20), 'transferability_category'] = 'Moderately Transferable'
    result_df.loc[result_df['total'] == 0, 'transferability_category'] = 'Terminal/Capstone'

    return result_df


def save_degree_results(school, degree, module_analysis_df, relevant_jobs_df, output_dir):
    """Save analysis results for a specific degree."""
    degree_dir = output_dir / school / degree
    degree_dir.mkdir(parents=True, exist_ok=True)

    # Save module analysis
    module_path = degree_dir / "module_analysis_results.csv"
    module_analysis_df.to_csv(module_path, index=False)

    # Save relevant jobs (subset of columns)
    jobs_path = degree_dir / "relevant_jobs.csv"
    save_cols = ['title', 'description']
    if 'companyName' in relevant_jobs_df.columns:
        save_cols.insert(1, 'companyName')
    elif 'company' in relevant_jobs_df.columns:
        save_cols.insert(1, 'company')

    # Add any computed columns
    for col in ['semantic_avg_similarity', 'skill_votes', 'skill_coverage']:
        if col in relevant_jobs_df.columns:
            save_cols.append(col)

    relevant_jobs_df[save_cols].to_csv(jobs_path, index=False)

    return degree_dir


def create_summary_table(all_results):
    """
    Create a summary comparison table from all degree results.

    Args:
        all_results: List of dicts with keys (school, degree, metrics)

    Returns:
        DataFrame with summary statistics
    """
    summary_rows = []

    for result in all_results:
        school = result['school']
        degree = result['degree']
        metrics = result['metrics']
        module_stats = result['module_stats']

        summary_rows.append({
            'school': school.upper(),
            'degree': degree.replace('_', ' ').title(),
            'num_modules': module_stats['num_modules'],
            'market_size': metrics['market_size'],
            'union_relevance': metrics['union_relevance'],
            'collective_relevance': metrics['collective_relevance'],
            'active_utilization_%': metrics['active_utilization'],
            'niche_utilization_%': metrics['niche_utilization'],
            'well_prepared_%': metrics['well_prepared_pct'],
            'top_module': module_stats['top_module'],
            'top_module_score': module_stats['top_module_score']
        })

    return pd.DataFrame(summary_rows)


def print_degree_summary(school, degree, metrics, module_analysis_df, config):
    """Print a formatted summary for a degree analysis."""
    degree_name = config.get_degree_full_name(school, degree)

    print("\n" + "=" * 80)
    print(f"{degree_name}")
    print("=" * 80)

    print(f"\n📊 Market Metrics:")
    print(f"  • Relevant Jobs: {metrics['market_size']:,}")
    print(f"  • Union Relevance: {metrics['union_relevance']:.3f}")
    print(f"  • Collective Relevance: {metrics['collective_relevance']:.3f}")

    print(f"\n🎯 Module Utilization:")
    print(f"  • Active Core: {metrics['active_utilization']:.1f}%")
    print(f"  • Niche/Supporting: {metrics['niche_utilization']:.1f}%")

    print(f"\n✅ Job Preparation:")
    print(f"  • Well Prepared: {metrics['well_prepared_jobs']} jobs ({metrics['well_prepared_pct']:.1f}%)")

    # Top 3 modules
    top_3 = module_analysis_df.nlargest(3, 'relevance_score')
    print(f"\n🏆 Top 3 Most Relevant Modules:")
    for idx, row in top_3.iterrows():
        print(f"  • {row['module_code']}: {row['relevance_score']:.3f}")


# ============================================
# HYBRID ANALYSIS: PREREQUISITE + JOB ALIGNMENT
# ============================================

def calculate_prerequisite_centrality(module_analysis_df, prereq_csv_path, include_transitive=True):
    """
    Calculate prerequisite centrality metrics for modules.

    Args:
        module_analysis_df: DataFrame with module analysis
        prereq_csv_path: Path to prerequisite counts CSV
        include_transitive: Whether to include transitive dependencies

    Returns:
        DataFrame with added centrality columns:
        - direct_dependents: Immediate modules that require this as prerequisite
        - transitive_dependents: All modules reachable through prerequisite chain
        - centrality_score: Combined centrality metric
    """
    if not prereq_csv_path.exists():
        # No prerequisite data - return zeros
        module_analysis_df['direct_dependents'] = 0
        module_analysis_df['transitive_dependents'] = 0
        module_analysis_df['centrality_score'] = 0
        return module_analysis_df

    prereq_df = pd.read_csv(prereq_csv_path)

    # Merge to get direct dependent counts
    result_df = module_analysis_df.merge(
        prereq_df[['module', 'total']],
        left_on='module_code',
        right_on='module',
        how='left'
    )

    result_df['direct_dependents'] = result_df['total'].fillna(0).astype(int)

    # For now, use direct as proxy for transitive
    # In future: build dependency graph and calculate transitive closure
    if include_transitive:
        # Approximate: transitive ≈ direct * growth factor
        # Modules with many direct dependents likely have even more transitive
        result_df['transitive_dependents'] = (result_df['direct_dependents'] * 1.5).astype(int)
    else:
        result_df['transitive_dependents'] = result_df['direct_dependents']

    # Combined centrality score (weighted)
    result_df['centrality_score'] = (
        0.6 * result_df['direct_dependents'] +
        0.4 * result_df['transitive_dependents']
    )

    # Clean up merge artifacts
    if 'total' in result_df.columns:
        result_df = result_df.drop(columns=['total'])
    if 'module' in result_df.columns and 'module' != 'module_code':
        result_df = result_df.drop(columns=['module'])

    return result_df


def classify_modules_hybrid(module_analysis_df, config):
    """
    Classify modules into 4 buckets based on job alignment + prerequisite centrality.

    Buckets:
    1. High alignment + high centrality → Core market-ready foundations
    2. High alignment + low centrality → Specialized market skills
    3. Low alignment + high centrality → Foundational prerequisites
    4. Low alignment + low centrality → Peripheral modules

    Args:
        module_analysis_df: DataFrame with relevance_score and centrality_score
        config: Config module with HYBRID_ANALYSIS settings

    Returns:
        DataFrame with added 'hybrid_bucket' column
    """
    align_threshold = config.HYBRID_ANALYSIS['alignment_threshold_high']
    central_threshold = config.HYBRID_ANALYSIS['centrality_threshold_high']

    def classify_module(row):
        high_align = row['relevance_score'] >= align_threshold
        high_central = row['centrality_score'] >= central_threshold

        if high_align and high_central:
            return 'high_align_high_central'
        elif high_align and not high_central:
            return 'high_align_low_central'
        elif not high_align and high_central:
            return 'low_align_high_central'
        else:
            return 'low_align_low_central'

    module_analysis_df['hybrid_bucket'] = module_analysis_df.apply(classify_module, axis=1)

    # Add human-readable names
    bucket_names = {k: v['name'] for k, v in config.MODULE_BUCKETS.items()}
    module_analysis_df['hybrid_bucket_name'] = module_analysis_df['hybrid_bucket'].map(bucket_names)

    return module_analysis_df


def analyze_prerequisite_scaffolding(module_analysis_df, config):
    """
    Generate insights about how job-relevant capabilities are scaffolded in curriculum.

    Returns:
        dict with scaffolding metrics and interpretation
    """
    bucket_counts = module_analysis_df['hybrid_bucket'].value_counts()
    total_modules = len(module_analysis_df)

    # Key metrics
    core_foundations = bucket_counts.get('high_align_high_central', 0)
    specialized_skills = bucket_counts.get('high_align_low_central', 0)
    foundational_prereqs = bucket_counts.get('low_align_high_central', 0)
    peripheral = bucket_counts.get('low_align_low_central', 0)

    # Calculate percentages
    pct_core = (core_foundations / total_modules) * 100 if total_modules > 0 else 0
    pct_specialized = (specialized_skills / total_modules) * 100 if total_modules > 0 else 0
    pct_foundational = (foundational_prereqs / total_modules) * 100 if total_modules > 0 else 0
    pct_peripheral = (peripheral / total_modules) * 100 if total_modules > 0 else 0

    # Interpretation
    if pct_core > 25:
        scaffolding_type = "Deeply Scaffolded"
        interpretation = "Job-relevant capabilities are well-integrated and progressively built through foundational modules."
    elif pct_specialized > 30:
        scaffolding_type = "Concentrated"
        interpretation = "Market-relevant skills are concentrated in standalone modules, with less prerequisite scaffolding."
    elif pct_foundational > 30:
        scaffolding_type = "Foundation-Heavy"
        interpretation = "Strong structural foundations exist, but may be indirectly connected to market outcomes."
    else:
        scaffolding_type = "Balanced"
        interpretation = "Mixed approach with both scaffolded and standalone market-relevant modules."

    return {
        'scaffolding_type': scaffolding_type,
        'interpretation': interpretation,
        'core_foundations_count': core_foundations,
        'core_foundations_pct': pct_core,
        'specialized_skills_count': specialized_skills,
        'specialized_skills_pct': pct_specialized,
        'foundational_prereqs_count': foundational_prereqs,
        'foundational_prereqs_pct': pct_foundational,
        'peripheral_count': peripheral,
        'peripheral_pct': pct_peripheral,
        'bucket_distribution': bucket_counts.to_dict()
    }


def print_hybrid_analysis_summary(module_analysis_df, scaffolding_metrics, config):
    """Print formatted summary of hybrid prerequisite + alignment analysis."""

    print("\n" + "=" * 80)
    print("HYBRID ANALYSIS: Prerequisite Scaffolding of Job-Relevant Capabilities")
    print("=" * 80)

    print(f"\n📐 Scaffolding Type: {scaffolding_metrics['scaffolding_type']}")
    print(f"💡 Interpretation: {scaffolding_metrics['interpretation']}")

    print(f"\n📊 Module Distribution:")

    for bucket_key, bucket_info in config.MODULE_BUCKETS.items():
        count = scaffolding_metrics['bucket_distribution'].get(bucket_key, 0)
        pct = (count / len(module_analysis_df)) * 100 if len(module_analysis_df) > 0 else 0
        print(f"\n  {bucket_info['name']} ({count} modules, {pct:.1f}%)")
        print(f"    → {bucket_info['description']}")

        # Show top 3 modules in this bucket
        bucket_modules = module_analysis_df[module_analysis_df['hybrid_bucket'] == bucket_key]
        if len(bucket_modules) > 0:
            top_3 = bucket_modules.nlargest(3, 'relevance_score')
            for _, mod in top_3.iterrows():
                print(f"      • {mod['module_code']}: align={mod['relevance_score']:.3f}, central={mod['centrality_score']:.0f}")


def create_hybrid_visualization(module_analysis_df, output_path, config):
    """
    Create 2x2 scatter plot of job alignment vs prerequisite centrality.

    Args:
        module_analysis_df: DataFrame with relevance_score and centrality_score
        output_path: Path to save visualization
        config: Config module
    """
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        fig, ax = plt.subplots(figsize=config.VIZ_SETTINGS['figsize_default'])

        # Color by bucket
        bucket_colors = {
            'high_align_high_central': '#2ecc71',    # Green
            'high_align_low_central': '#f39c12',     # Orange
            'low_align_high_central': '#3498db',     # Blue
            'low_align_low_central': '#95a5a6'       # Gray
        }

        for bucket, color in bucket_colors.items():
            bucket_data = module_analysis_df[module_analysis_df['hybrid_bucket'] == bucket]
            if len(bucket_data) > 0:
                bucket_name = config.MODULE_BUCKETS[bucket]['name']
                ax.scatter(
                    bucket_data['relevance_score'],
                    bucket_data['centrality_score'],
                    c=color,
                    label=bucket_name,
                    alpha=0.6,
                    s=100
                )

        # Draw threshold lines
        align_thresh = config.HYBRID_ANALYSIS['alignment_threshold_high']
        central_thresh = config.HYBRID_ANALYSIS['centrality_threshold_high']

        ax.axvline(align_thresh, color='red', linestyle='--', alpha=0.5, linewidth=1)
        ax.axhline(central_thresh, color='red', linestyle='--', alpha=0.5, linewidth=1)

        # Annotate top modules
        top_modules = module_analysis_df.nlargest(10, 'relevance_score')
        for _, mod in top_modules.iterrows():
            ax.annotate(
                mod['module_code'],
                (mod['relevance_score'], mod['centrality_score']),
                fontsize=8,
                alpha=0.7
            )

        ax.set_xlabel('Job Alignment Score (Relevance)', fontsize=12)
        ax.set_ylabel('Prerequisite Centrality (Structural Importance)', fontsize=12)
        ax.set_title('Hybrid Analysis: Market Relevance × Curriculum Structure', fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=config.VIZ_SETTINGS['dpi'], bbox_inches='tight')
        plt.close()

        return True
    except Exception as e:
        print(f"⚠️  Could not create hybrid visualization: {e}")
        return False


def run_hybrid_analysis(module_analysis_df, prereq_csv_path, output_dir, config):
    """
    Run complete hybrid analysis: prerequisite centrality + job alignment.

    This is the main entry point for the hybrid analysis extension.

    Args:
        module_analysis_df: DataFrame with module metrics
        prereq_csv_path: Path to prerequisite data
        output_dir: Directory to save outputs
        config: Config module

    Returns:
        Updated module_analysis_df with hybrid metrics
    """
    if not config.HYBRID_ANALYSIS['enabled']:
        print("\n⏭️  Hybrid analysis disabled in config")
        return module_analysis_df

    print("\n" + "=" * 80)
    print("Running Hybrid Analysis (Extension Layer)")
    print("=" * 80)

    # Step 1: Calculate centrality
    module_analysis_df = calculate_prerequisite_centrality(
        module_analysis_df,
        prereq_csv_path,
        include_transitive=config.HYBRID_ANALYSIS['include_transitive']
    )

    # Step 2: Classify into buckets
    module_analysis_df = classify_modules_hybrid(module_analysis_df, config)

    # Step 3: Analyze scaffolding
    scaffolding_metrics = analyze_prerequisite_scaffolding(module_analysis_df, config)

    # Step 4: Print summary
    print_hybrid_analysis_summary(module_analysis_df, scaffolding_metrics, config)

    # Step 5: Create visualization
    viz_path = output_dir / "hybrid_analysis_2x2.png"
    create_hybrid_visualization(module_analysis_df, viz_path, config)

    # Step 6: Save detailed results
    hybrid_summary_path = output_dir / "hybrid_scaffolding_summary.csv"
    pd.DataFrame([scaffolding_metrics]).to_csv(hybrid_summary_path, index=False)

    print(f"\n✅ Hybrid analysis complete")
    print(f"   • Visualization: {viz_path}")
    print(f"   • Summary: {hybrid_summary_path}")

    return module_analysis_df
