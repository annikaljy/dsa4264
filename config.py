"""
Configuration file for Degree-to-Job Market Analysis
=====================================================
Centralized configuration for paths, schools, and degrees.
"""

import os
from pathlib import Path

# ============================================
# BASE PATHS
# ============================================
# Project root directory
PROJECT_ROOT = Path(__file__).parent

# Data directory (can be external - recommended for large files)
# To use external directory: DATA_DIR = Path.home() / "dsa4264_data"
DATA_DIR = PROJECT_ROOT / "outputs"

# ============================================
# INPUT DATA PATHS
# ============================================
# Job market embeddings (large file - should be in external data dir)
JOBS_PARQUET = DATA_DIR / "processed_jobs_dual_embeddings.parquet"

# School-specific embedded modules
SCHOOL_EMBEDDINGS = {
    "nus": DATA_DIR / "nus" / "nus-embeddings",
    "smu": DATA_DIR / "smu" / "smu-embeddings",
    "sutd": DATA_DIR / "sutd" / "sutd-embeddings"
}

# Prerequisite counts (if available)
PREREQ_DATA_DIR = DATA_DIR / "mod_importance"

# ============================================
# OUTPUT PATHS
# ============================================
# Global analysis (run once for entire job market)
GLOBAL_OUTPUT_DIR = DATA_DIR / "bertopic_visualizations_global"

# School-specific analysis outputs
ANALYSIS_OUTPUT_DIR = DATA_DIR / "analysis_results"

# Summary outputs (for final report)
SUMMARY_OUTPUT_DIR = DATA_DIR / "summary"

# ============================================
# DEGREE CONFIGURATIONS
# ============================================
DEGREES = {
    "nus": {
        "name": "National University of Singapore",
        "degrees": {
            "data_sci_analytics": {
                "name": "Data Science and Analytics",
                "category": "data_science"
            },
            "business_analytics": {
                "name": "Business Analytics",
                "category": "business_analytics"
            },
            "information_systems": {
                "name": "Information Systems",
                "category": "information_systems"
            },
            "biomedical_engineering": {
                "name": "Biomedical Engineering",
                "category": "engineering"
            },
            "chemical_engineering": {
                "name": "Chemical Engineering",
                "category": "engineering"
            },
            "civil_engineering": {
                "name": "Civil Engineering",
                "category": "engineering"
            },
            "accountancy": {
                "name": "Accountancy",
                "category": "business"
            },
            "industrial_design": {
                "name": "Industrial Design",
                "category": "design"
            },
            "landscape_architecture": {
                "name": "Landscape Architecture",
                "category": "design"
            },
            "real_estate": {
                "name": "Real Estate",
                "category": "business"
            }
        }
    },
    "smu": {
        "name": "Singapore Management University",
        "degrees": {
            "accountancy": {
                "name": "Accountancy",
                "category": "business"
            },
            "business": {
                "name": "Business",
                "category": "business"
            },
            "computinglaw": {
                "name": "Computing and Law",
                "category": "information_systems"
            },
            "economics": {
                "name": "Economics",
                "category": "business"
            },
            "information_systems": {
                "name": "Information Systems",
                "category": "information_systems"
            },
            "social_sciences": {
                "name": "Social Sciences",
                "category": "social_sciences"
            }
        }
    },
    "sutd": {
        "name": "Singapore University of Technology and Design",
        "degrees": {
            "architecture": {
                "name": "Architecture and Sustainable Design",
                "category": "design"
            },
            "computer_sci": {
                "name": "Computer Science and Design",
                "category": "data_science"
            },
            "design_ai": {
                "name": "Design and AI",
                "category": "data_science"
            },
            "engineering_product": {
                "name": "Engineering Product Development",
                "category": "engineering"
            },
            "engineering_systems": {
                "name": "Engineering Systems and Design",
                "category": "engineering"
            }
        }
    }
}

# ============================================
# ANALYSIS PARAMETERS
# ============================================
# NUSMods API settings
START_YEAR = 2025  # Only use 2025-2026 academic year
FALLBACK_YEARS = []  # No fallback - if not in 2025-2026, drop it
DROP_MISSING_DESCRIPTIONS = True  # Drop modules without descriptions

# Employment types to include
ALLOWED_EMPLOYMENT_TYPES = {"Full Time", "Permanent", "Contract"}

# Similarity thresholds (data-driven approach)
# These are used as defaults but can be overridden by percentile-based methods
THRESHOLDS = {
    "skill_vote": 0.5,           # For approval voting
    "semantic_match": 0.45,      # For semantic similarity
    "breadth_percentile": 60     # Percentile for breadth analysis
}

# BERTopic optimization
BERTOPIC_TRIALS = 10  # Number of Optuna trials for hyperparameter tuning

# Stop words for topic modeling
JOB_STOPWORDS = [
    "job", "description", "apply", "candidates", "interested", "hiring",
    "qualifications", "preferred", "required", "responsibilities", "equivalent",
    "company", "opportunities", "role", "title", "experience", "years", "year",
    "skills", "work", "working", "team", "teams", "knowledge", "ability", "strong",
    "using", "understanding", "including", "related", "key", "help", "plus"
]

# ============================================
# HYBRID ANALYSIS: PREREQUISITE + JOB ALIGNMENT
# ============================================
# Extension layer for interpreting prerequisite scaffolding of job-relevant capabilities
HYBRID_ANALYSIS = {
    "enabled": True,  # Set to False to skip this analysis
    "alignment_threshold_high": 0.25,  # Above this = "High alignment"
    "centrality_threshold_high": 10,    # Above this = "High centrality" (prerequisite count)
    "include_transitive": True,         # Calculate transitive dependencies if data available
}

# Module classification buckets
MODULE_BUCKETS = {
    "high_align_high_central": {
        "name": "Core Market-Ready Foundations",
        "description": "Strongest modules - both job-relevant and deeply scaffolded in curriculum"
    },
    "high_align_low_central": {
        "name": "Specialized Market Skills",
        "description": "Valuable but possibly isolated - often electives or advanced topics"
    },
    "low_align_high_central": {
        "name": "Foundational Prerequisites",
        "description": "Structurally important but indirect - math/stats/programming basics"
    },
    "low_align_low_central": {
        "name": "Peripheral Modules",
        "description": "Less influential in both structure and market alignment"
    }
}

# ============================================
# VISUALIZATION SETTINGS
# ============================================
VIZ_SETTINGS = {
    "dpi": 300,
    "figsize_default": (12, 8),
    "figsize_wide": (16, 8),
    "style": "whitegrid",
    "palette": "husl",
    "top_n_modules": 15
}

# ============================================
# REPRESENTATIVE DEGREES FOR SUMMARY
# ============================================
# Select representative degrees from each category for detailed reporting
REPRESENTATIVE_DEGREES = {
    "data_science": [
        ("nus", "data_sci_analytics"),
        ("sutd", "computer_sci")
    ],
    "business_analytics": [
        ("nus", "business_analytics")
    ],
    "information_systems": [
        ("nus", "information_systems"),
        ("smu", "information_systems")
    ],
    "engineering": [
        ("nus", "biomedical_engineering"),
        ("sutd", "engineering_systems")
    ],
    "business": [
        ("smu", "business"),
        ("nus", "accountancy")
    ]
}

# ============================================
# HELPER FUNCTIONS
# ============================================
def get_degree_embeddings_path(school: str, degree: str) -> Path:
    """Get the path to degree-specific embeddings parquet file."""
    embeddings_dir = SCHOOL_EMBEDDINGS.get(school)
    if not embeddings_dir:
        raise ValueError(f"Unknown school: {school}")

    return embeddings_dir / f"{degree}_modules_embeddings.parquet"


def get_degree_output_dir(school: str, degree: str) -> Path:
    """Get the output directory for a specific school-degree combination."""
    output_dir = ANALYSIS_OUTPUT_DIR / school / degree
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def get_degree_full_name(school: str, degree: str) -> str:
    """Get the full display name for a degree."""
    school_data = DEGREES.get(school, {})
    degree_data = school_data.get("degrees", {}).get(degree, {})
    school_name = school_data.get("name", school.upper())
    degree_name = degree_data.get("name", degree.replace("_", " ").title())
    return f"{school_name} - {degree_name}"


def get_all_degrees():
    """Get list of all (school, degree) tuples."""
    all_degrees = []
    for school, school_data in DEGREES.items():
        for degree in school_data["degrees"].keys():
            all_degrees.append((school, degree))
    return all_degrees


def get_degrees_by_category(category: str):
    """Get list of (school, degree) tuples for a specific category."""
    matching = []
    for school, school_data in DEGREES.items():
        for degree, degree_data in school_data["degrees"].items():
            if degree_data.get("category") == category:
                matching.append((school, degree))
    return matching


# ============================================
# ENVIRONMENT VALIDATION
# ============================================
def validate_environment():
    """Validate that required files and directories exist."""
    issues = []

    # Check jobs data
    if not JOBS_PARQUET.exists():
        issues.append(f"Missing job embeddings: {JOBS_PARQUET}")

    # Check school embeddings directories
    for school, path in SCHOOL_EMBEDDINGS.items():
        if not path.exists():
            issues.append(f"Missing embeddings directory for {school}: {path}")

    return issues


if __name__ == "__main__":
    # Print configuration summary
    print("=" * 80)
    print("CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"\nProject Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"\nTotal Schools: {len(DEGREES)}")

    for school, school_data in DEGREES.items():
        print(f"\n{school.upper()}: {school_data['name']}")
        print(f"  Degrees: {len(school_data['degrees'])}")
        for degree, degree_data in school_data['degrees'].items():
            print(f"    - {degree}: {degree_data['name']} [{degree_data['category']}]")

    print(f"\nTotal Degrees: {len(get_all_degrees())}")

    print("\n" + "=" * 80)
    print("ENVIRONMENT VALIDATION")
    print("=" * 80)
    issues = validate_environment()
    if issues:
        print("\nISSUES FOUND:")
        for issue in issues:
            print(f"  ⚠️  {issue}")
    else:
        print("\n✅ All required files and directories found!")
