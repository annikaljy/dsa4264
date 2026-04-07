"""
Test script to verify all data and analysis functions work correctly.
Run this before using notebooks to ensure no errors.
"""

import sys
import config
import analysis_utils as au
import pandas as pd
import numpy as np

def test_data_availability():
    """Test that all required data files exist."""
    print("=" * 80)
    print("TEST 1: DATA AVAILABILITY")
    print("=" * 80)

    issues = []

    # Test jobs data
    print(f"\n✓ Jobs data: {config.JOBS_PARQUET}")
    if not config.JOBS_PARQUET.exists():
        issues.append("Jobs parquet file missing")
    else:
        try:
            jobs_df = pd.read_parquet(config.JOBS_PARQUET)
            print(f"  → {len(jobs_df):,} jobs loaded")
            if 'embedding_mpnet' not in jobs_df.columns:
                issues.append("Jobs data missing 'embedding_mpnet' column")
        except Exception as e:
            issues.append(f"Cannot load jobs data: {e}")

    # Test each school's embeddings
    for school in ['nus', 'smu', 'sutd']:
        print(f"\n✓ {school.upper()} embeddings:")
        school_dir = config.SCHOOL_EMBEDDINGS[school]

        if not school_dir.exists():
            issues.append(f"{school.upper()} embeddings directory missing")
            continue

        degrees = config.DEGREES[school]['degrees']
        for degree_key in degrees.keys():
            try:
                embeddings_path = config.get_degree_embeddings_path(school, degree_key)
                if embeddings_path.exists():
                    df = pd.read_parquet(embeddings_path)
                    print(f"  → {degree_key}: {len(df)} modules")
                else:
                    issues.append(f"{school}/{degree_key} embeddings missing")
            except Exception as e:
                issues.append(f"Error loading {school}/{degree_key}: {e}")

    # Test prerequisite data
    print(f"\n✓ Prerequisite data: {config.PREREQ_DATA_DIR}")
    if config.PREREQ_DATA_DIR.exists():
        prereq_files = list(config.PREREQ_DATA_DIR.glob("*.csv"))
        print(f"  → {len(prereq_files)} prerequisite files found")

        # Note which schools have prerequisite data
        nus_prereq = [f for f in prereq_files if any(
            d in f.name for d in config.DEGREES['nus']['degrees'].keys()
        )]
        print(f"  → NUS: {len(nus_prereq)} degrees with prerequisite data")
        print(f"  → SMU/SUTD: Prerequisite data not available (hybrid analysis will skip)")
    else:
        print(f"  → Directory not found (hybrid analysis will be disabled)")

    if issues:
        print("\n" + "=" * 80)
        print("❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    else:
        print("\n" + "=" * 80)
        print("✅ ALL DATA FILES AVAILABLE")
        return True


def test_analysis_functions():
    """Test that analysis functions work correctly."""
    print("\n" + "=" * 80)
    print("TEST 2: ANALYSIS FUNCTIONS")
    print("=" * 80)

    try:
        # Load test data
        print("\n1. Loading test degree (NUS Data Science & Analytics)...")
        modules_df = au.load_degree_modules('nus', 'data_sci_analytics', config)
        print(f"   ✓ Loaded {len(modules_df)} modules")

        print("\n2. Extracting module embeddings...")
        module_embeddings = au.extract_embeddings(modules_df)
        print(f"   ✓ Extracted embeddings: shape {module_embeddings.shape}")

        print("\n3. Loading jobs data...")
        jobs_df = pd.read_parquet(config.JOBS_PARQUET)
        print(f"   ✓ Loaded {len(jobs_df):,} jobs")

        print("\n4. Filtering jobs by employment type...")
        filtered_jobs = au.filter_jobs_by_employment_type(jobs_df)
        print(f"   ✓ Filtered to {len(filtered_jobs):,} jobs")

        print("\n5. Extracting job embeddings...")
        job_embeddings = au.extract_embeddings(filtered_jobs)
        print(f"   ✓ Extracted embeddings: shape {job_embeddings.shape}")

        print("\n6. Calculating approval voting...")
        similarity_matrix, votes, avg_sim = au.calculate_approval_voting(
            module_embeddings,
            job_embeddings,
            threshold=0.5
        )
        print(f"   ✓ Similarity matrix: shape {similarity_matrix.shape}")
        print(f"   ✓ Average votes per job: {votes.mean():.2f}")
        print(f"   ✓ Average similarity: {avg_sim.mean():.3f}")

        print("\n7. Finding relevant job market (using Kneedle)...")
        filtered_jobs['_temp_sim'] = avg_sim
        relevant_jobs, cutoff_idx, cutoff_score = au.find_relevant_job_market(
            filtered_jobs,
            avg_sim,
            method='kneedle'
        )
        print(f"   ✓ Relevant jobs: {len(relevant_jobs):,}")
        print(f"   ✓ Cutoff score: {cutoff_score:.4f}")

        print("\n8. Analyzing modules...")
        module_analysis = au.analyze_modules(
            modules_df,
            relevant_jobs,
            similarity_matrix,
            breadth_percentile=60
        )
        print(f"   ✓ Analyzed {len(module_analysis)} modules")
        print(f"   ✓ Top module: {module_analysis.nlargest(1, 'relevance_score').iloc[0]['module_code']}")
        print(f"   ✓ Max relevance: {module_analysis['relevance_score'].max():.3f}")

        print("\n9. Calculating degree metrics...")
        metrics = au.calculate_degree_metrics(
            modules_df,
            relevant_jobs,
            similarity_matrix
        )
        print(f"   ✓ Market size: {metrics['market_size']:,}")
        print(f"   ✓ Union relevance: {metrics['union_relevance']:.3f}")
        print(f"   ✓ Collective relevance: {metrics['collective_relevance']:.3f}")

        print("\n10. Testing hybrid analysis (if prerequisite data available)...")
        prereq_path = config.PREREQ_DATA_DIR / "data_sci_analytics_counts.csv"
        if prereq_path.exists():
            module_analysis = au.calculate_prerequisite_centrality(
                module_analysis,
                prereq_path,
                include_transitive=True
            )
            print(f"   ✓ Added centrality scores")

            module_analysis = au.classify_modules_hybrid(module_analysis, config)
            print(f"   ✓ Classified into buckets")
            print(f"   ✓ Distribution: {module_analysis['hybrid_bucket'].value_counts().to_dict()}")
        else:
            print(f"   ⚠ Skipped (no prerequisite data for this degree)")

        print("\n" + "=" * 80)
        print("✅ ALL ANALYSIS FUNCTIONS WORKING")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multi_school():
    """Test loading data from all schools."""
    print("\n" + "=" * 80)
    print("TEST 3: MULTI-SCHOOL DATA LOADING")
    print("=" * 80)

    test_degrees = [
        ('nus', 'data_sci_analytics'),
        ('smu', 'business'),
        ('sutd', 'computer_sci')
    ]

    all_passed = True
    for school, degree in test_degrees:
        try:
            modules_df = au.load_degree_modules(school, degree, config)
            embeddings = au.extract_embeddings(modules_df)
            degree_name = config.get_degree_full_name(school, degree)
            print(f"✓ {degree_name}: {len(modules_df)} modules, embedding shape {embeddings.shape}")
        except Exception as e:
            print(f"✗ {school}/{degree}: {e}")
            all_passed = False

    if all_passed:
        print("\n" + "=" * 80)
        print("✅ ALL SCHOOLS DATA ACCESSIBLE")
        return True
    else:
        print("\n" + "=" * 80)
        print("❌ SOME SCHOOLS FAILED")
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " COMPREHENSIVE DATA & ANALYSIS TEST ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")

    results = []

    # Test 1: Data availability
    results.append(("Data Availability", test_data_availability()))

    # Test 2: Analysis functions
    results.append(("Analysis Functions", test_analysis_functions()))

    # Test 3: Multi-school loading
    results.append(("Multi-School Loading", test_multi_school()))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<60} {status}")
        if not passed:
            all_passed = False

    print("=" * 80)

    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Ready to run analysis.")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED. Please fix issues before running analysis.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
