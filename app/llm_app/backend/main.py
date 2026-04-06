import os
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import uvicorn

app = FastAPI(title="MOE Course Matcher API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR        = "/app/data"
embedding_model = None
all_modules_df  = None


@app.on_event("startup")
def load_models():
    global embedding_model, all_modules_df

    print("Loading MPNet embedding model...")
    embedding_model = SentenceTransformer("all-mpnet-base-v2")

    print("Loading module embeddings...")
    all_modules_df = pd.read_parquet(
        os.path.join(DATA_DIR, "all_universities_embedded.parquet")
    )
    if "skill_embedding" not in all_modules_df.columns and "embedding" in all_modules_df.columns:
        all_modules_df = all_modules_df.rename(columns={"embedding": "skill_embedding"})

    # Ensure school column exists (fallback to "NUS" for old parquets)
    if "school" not in all_modules_df.columns:
        all_modules_df["school"] = "NUS"

    # ── Drop unwanted NUS faculties ──
    # For NUS, both 'faculty' and 'course' hold the faculty name (they're set equal at build time)
    EXCLUDE_FACULTIES = {
        "NUS-ISS",
        "Cont and Lifelong Education",
        "Multi Disciplinary Programme",
        "Duke-NUS Medical School",
        "SSH School of Public Health",
    }
    before   = len(all_modules_df)
    nus_mask = all_modules_df["school"] == "NUS"
    # Filter on whichever column is available
    check_col = "faculty" if "faculty" in all_modules_df.columns else "course"
    exclude_mask = all_modules_df[check_col].isin(EXCLUDE_FACULTIES)
    all_modules_df = all_modules_df[~(nus_mask & exclude_mask)].reset_index(drop=True)
    dropped = before - len(all_modules_df)
    if dropped:
        print(f"Filtered out {dropped} modules from excluded NUS faculties ({check_col} col).")

    print(f"Ready — {len(all_modules_df)} modules loaded.")
    print(all_modules_df.groupby("school").size().rename("modules").to_string())


# ── Course display name mappings ─────────────────────────
COURSE_NAMES = {
    # SUTD
    "architecture":          "Architecture and Sustainable Design (ASD)",
    "design_ai":             "Design and Artificial Intelligence (DAI)",
    "engineering_product":   "Engineering Product Development (EPD)",
    "engineering_systems":   "Engineering Systems and Design (ESD)",
    "computer_sci":          "Computer Science and Design (CSD)",
    # SMU
    "economics":             "Economics",
    "accountancy":           "Accountancy",
    "business":              "Business Management",
    "computinglaw":          "Computing & Law",
    "information_systems":   "Information Systems",
    "social_sciences":       "Social Sciences",
}

def display_course(raw: str) -> str:
    return COURSE_NAMES.get(str(raw).strip(), raw)


# ── Core matcher ──────────────────────────────────────────
def match_courses(job_text: str, top_n: int = 10) -> dict:
    # 1. Embed job
    job_emb  = embedding_model.encode([job_text])
    mod_embs = np.stack(all_modules_df["skill_embedding"].values)
    sims     = cosine_similarity(job_emb, mod_embs).flatten()

    mdf = all_modules_df.copy()
    mdf["similarity"] = sims

    # 2. Top modules — school-aware so SMU/SUTD aren't crowded out by NUS volume
    # Strategy: top 5 globally + top 2 from each non-NUS school (deduplicated)
    cols = ["code", "title", "school", "course", "description", "similarity"]
    sorted_mdf = mdf.sort_values("similarity", ascending=False)

    top_global = sorted_mdf.head(5)[cols].copy()

    per_school = []
    for school_name in sorted_mdf["school"].unique():
        if school_name == "NUS":
            continue
        school_top = (
            sorted_mdf[sorted_mdf["school"] == school_name]
            .head(2)[cols]
            .copy()
        )
        per_school.append(school_top)

    if per_school:
        top_modules_df = pd.concat([top_global] + per_school, ignore_index=True)
        top_modules_df = top_modules_df.drop_duplicates(subset=["code"])
        top_modules_df = top_modules_df.sort_values("similarity", ascending=False).head(15)
    else:
        top_modules_df = sorted_mdf.head(10)[cols].copy()

    top_modules_df["course"] = top_modules_df["course"].apply(display_course)
    top_modules = top_modules_df.to_dict(orient="records")

    # 3. Aggregate by school + course
    courses = []
    for (school, course_name), grp in mdf.groupby(["school", "course"]):
        best_row = grp.loc[grp["similarity"].idxmax()]
        courses.append({
            "school":              school,
            "course":              display_course(course_name),
            "avg_score":           float(grp["similarity"].mean()),
            "max_score":           float(grp["similarity"].max()),
            "n_relevant_modules":  int((grp["similarity"] >= 0.45).sum()),
            "best_module_code":    str(best_row["code"]),
            "best_module_title":   str(best_row["title"]),
        })

    course_df = pd.DataFrame(courses)
    course_df["score"] = 0.7 * course_df["avg_score"] + 0.3 * course_df["max_score"]
    course_df = course_df.sort_values("score", ascending=False).head(top_n)

    return {
        "top_courses": course_df.to_dict(orient="records"),
        "top_modules": top_modules,
    }


# ── Routes ────────────────────────────────────────────────
class TextRequest(BaseModel):
    job_title: str = ""
    job_text:  str
    top_n:     int = 10

@app.get("/health")
def health():
    n = len(all_modules_df) if all_modules_df is not None else 0
    return {"status": "ok", "modules_loaded": n}

@app.get("/debug/faculties")
def debug_faculties():
    """Returns every unique faculty/course value for NUS rows.
    Visit http://localhost:8000/debug/faculties to see exact strings in your parquet."""
    nus = all_modules_df[all_modules_df["school"] == "NUS"]
    result = {"course_col": nus["course"].value_counts().to_dict()}
    if "faculty" in nus.columns:
        result["faculty_col"] = nus["faculty"].value_counts().to_dict()
    return result

@app.post("/match/text")
def match_from_text(req: TextRequest):
    text = f"{req.job_title} {req.job_text}".strip()
    if not text:
        raise HTTPException(status_code=400, detail="job_text cannot be empty")
    result = match_courses(text, req.top_n)
    result["job_info"] = {"title": req.job_title, "description": req.job_text}
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
