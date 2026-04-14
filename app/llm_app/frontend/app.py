import base64
import os
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
MOE_LOGO_PATH = Path("assets") / "moe-logo.png"

DEMO_RESULT: Dict[str, Any] = {
    "job_info": {
        "title": "AI Product Analyst",
        "description": "Prototype LLM-powered analytics tools, evaluate models, and work with product and data teams.",
    },
    "top_courses": [
        {
            "school": "NUS",
            "course": "Business Analytics",
            "score": 0.89,
            "best_module_code": "BT3103",
            "best_module_title": "Application Systems Development",
            "n_relevant_modules": 8,
        },
        {
            "school": "SMU",
            "course": "Information Systems",
            "score": 0.82,
            "best_module_code": "IS215",
            "best_module_title": "Digital Business",
            "n_relevant_modules": 6,
        },
        {
            "school": "SUTD",
            "course": "Design and Artificial Intelligence (DAI)",
            "score": 0.78,
            "best_module_code": "DAI101",
            "best_module_title": "Human-Centered AI",
            "n_relevant_modules": 5,
        },
    ],
    "top_modules": [
        {
            "code": "BT3103",
            "title": "Application Systems Development",
            "school": "NUS",
            "course": "Business Analytics",
            "description": "Build data products and analytics systems with real-world business requirements.",
            "similarity": 0.91,
        },
        {
            "code": "IS215",
            "title": "Digital Business",
            "school": "SMU",
            "course": "Information Systems",
            "description": "Explore digital product strategy, platform thinking, and business transformation.",
            "similarity": 0.85,
        },
        {
            "code": "DAI101",
            "title": "Human-Centered AI",
            "school": "SUTD",
            "course": "Design and Artificial Intelligence (DAI)",
            "description": "Apply AI methods with a focus on design, usability, and responsible systems thinking.",
            "similarity": 0.80,
        },
    ],
}

CHAT_SUGGESTIONS = [
    "Which programme looks strongest for an AI product role?",
    "Why did SMU Information Systems rank highly?",
    "Compare the top NUS and SUTD options for data analytics.",
]


def format_pct(score: float) -> str:
    return f"{round(float(score or 0) * 100)}%"


def fetch_matches(api_base: str, job_title: str, job_text: str, top_n: int) -> Dict[str, Any]:
    response = requests.post(
        f"{api_base}/match/text",
        json={
            "job_title": job_title,
            "job_text": job_text,
            "top_n": top_n,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def fetch_chat(api_base: str, message: str, history: List[Dict[str, Any]], top_k: int = 6) -> Dict[str, Any]:
    payload_history = [
        {"role": item["role"], "content": item["content"]}
        for item in history
        if item.get("role") in {"user", "assistant"} and str(item.get("content", "")).strip()
    ][-8:]
    response = requests.post(
        f"{api_base}/chat",
        json={
            "message": message,
            "history": payload_history,
            "top_k": top_k,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def fetch_health(api_base: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(f"{api_base}/health", timeout=3)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def load_logo_data_uri(path: Path) -> str:
    resolved_path = path
    if not resolved_path.exists():
        resolved_path = Path(__file__).resolve().parent / path
    if not resolved_path.exists():
        return ""
    encoded = base64.b64encode(resolved_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def init_state() -> None:
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("result_source", None)
    st.session_state.setdefault("last_error", None)
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("chat_last_error", None)


def school_style(school: str) -> Dict[str, str]:
    styles = {
        "NUS": {"bg": "#E6F1FB", "fg": "#0C447C"},
        "SMU": {"bg": "#E7F7EE", "fg": "#0A5B45"},
        "SUTD": {"bg": "#FEF0D8", "fg": "#8A4B08"},
    }
    return styles.get(str(school).upper(), {"bg": "#F2EFE8", "fg": "#4B4B5F"})


def score_tone(score: float) -> Dict[str, str]:
    pct = float(score or 0)
    if pct >= 0.8:
        return {"bg": "#E7F7EE", "fg": "#166534"}
    if pct >= 0.6:
        return {"bg": "#FEF3C7", "fg": "#B7791F"}
    return {"bg": "#FDECEA", "fg": "#922B21"}


def render_course_cards(top_courses: List[Dict[str, Any]]) -> None:
    if not top_courses:
        st.markdown(
            """
            <div class="empty-state">
              <strong>No programme matches yet</strong>
              Run a search to populate the ranking cards.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    chunks = [(i, top_courses[i : i + 2]) for i in range(0, len(top_courses), 2)]
    for start_idx, chunk in chunks:
        columns = st.columns(len(chunk))
        for offset, (col, course) in enumerate(zip(columns, chunk), start=0):
            school = str(course.get("school", "NUS"))
            school_colors = school_style(school)
            score = float(course.get("score", 0))
            best_module = escape(str(course.get("best_module_code", "-")))
            course_name = escape(str(course.get("course", "Untitled programme")))
            school_name = escape(school)
            bar_pct = max(4, min(100, round(score * 100)))
            rank = start_idx + offset + 1

            with col:
                st.markdown(
                    f"""
                    <div class="course-card">
                      <div class="course-topline">
                        <span class="school-pill" style="background:{school_colors['bg']};color:{school_colors['fg']};">
                          {school_name}
                        </span>
                        <span class="rank-pill">Rank #{rank}</span>
                      </div>
                      <h3>{course_name}</h3>
                      <div class="course-metrics">
                        <div>
                          <div class="metric-label">Alignment Score</div>
                          <div class="metric-value">{format_pct(score)}</div>
                        </div>
                        <div>
                          <div class="metric-label">Relevant Modules</div>
                          <div class="metric-value">{int(course.get('n_relevant_modules', 0))}</div>
                        </div>
                      </div>
                      <div class="score-bar">
                        <span style="width:{bar_pct}%"></span>
                      </div>
                      <div class="best-module">
                        <span>Best module</span>
                        <strong>{best_module}</strong>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_summary_cards(top_courses: List[Dict[str, Any]], top_modules: List[Dict[str, Any]], source_label: str) -> None:
    best_match = f"{round(float(top_courses[0].get('score', 0)) * 100)}%" if top_courses else "0%"
    summary = [
        ("Programmes Ranked", str(len(top_courses))),
        ("Modules Surfaced", str(len(top_modules))),
        ("Source", escape(source_label)),
        ("Best Match", best_match),
    ]
    cols = st.columns(len(summary))
    for col, (label, value) in zip(cols, summary):
        with col:
            st.markdown(
                f"""
                <div class="summary-card">
                  <div class="summary-label">{label}</div>
                  <div class="summary-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_course_table(top_courses: List[Dict[str, Any]]) -> None:
    if not top_courses:
        st.markdown(
            """
            <div class="empty-state">
              <strong>No ranking table yet</strong>
              Programme rows will appear here after you run a search.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    body_rows = []
    for rank, course in enumerate(top_courses, start=1):
        school = str(course.get("school", "NUS"))
        school_colors = school_style(school)
        body_rows.append(
            "<tr>"
            f"<td>{rank}</td>"
            f"<td><span class='table-school-pill' style='background:{school_colors['bg']};color:{school_colors['fg']};'>{escape(school)}</span></td>"
            f"<td>{escape(str(course.get('course', 'Untitled programme')))}</td>"
            f"<td>{format_pct(course.get('score', 0))}</td>"
            f"<td>{escape(str(course.get('best_module_code', '-')))}</td>"
            f"<td>{int(course.get('n_relevant_modules', 0))}</td>"
            "</tr>"
        )

    table_html = (
        '<div class="ranking-table-wrap">'
        '<table class="ranking-table">'
        "<thead>"
        "<tr>"
        "<th>#</th>"
        "<th>School</th>"
        "<th>Programme</th>"
        "<th>Score</th>"
        "<th>Best Module</th>"
        "<th>Relevant Modules</th>"
        "</tr>"
        "</thead>"
        "<tbody>"
        + "".join(body_rows)
        + "</tbody>"
        "</table>"
        "</div>"
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_module_cards(top_modules: List[Dict[str, Any]]) -> None:
    if not top_modules:
        st.markdown(
            """
            <div class="empty-state">
              <strong>No module matches yet</strong>
              Module evidence will appear here after a successful match run.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    columns = st.columns(2)
    for idx, module in enumerate(top_modules):
        col = columns[idx % 2]
        similarity = float(module.get("similarity", 0))
        score_label = format_pct(similarity)
        school_colors = school_style(str(module.get("school", "NUS")))
        tone = score_tone(similarity)

        with col:
            st.markdown(
                f"""
                <div class="module-card">
                  <div class="module-meta">
                    <span class="module-code">{escape(str(module.get('code', '')))}</span>
                    <span class="module-school" style="background:{school_colors['bg']};color:{school_colors['fg']};">
                      {escape(str(module.get('school', 'NUS')))}
                    </span>
                  </div>
                  <h4>{escape(str(module.get('title', 'Untitled module')))}</h4>
                  <div class="module-course">{escape(str(module.get('course', '')))}</div>
                  <p>{escape(str(module.get('description', '')))}</p>
                  <div class="module-score" style="background:{tone['bg']};color:{tone['fg']};">{score_label} match</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_result(result: Dict[str, Any], api_base: str, source_label: str) -> None:
    top_courses = result.get("top_courses", [])
    top_modules = result.get("top_modules", [])
    job_info = result.get("job_info", {})

    st.markdown(
        f"""
        <div class="job-summary">
          <div class="label">Matched job</div>
          <div class="title">{escape(str(job_info.get('title') or 'Untitled role'))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_summary_cards(top_courses, top_modules, source_label)

    st.markdown(
        f"""
        <div class="result-meta">
          <span>Backend target: <code>{escape(api_base)}</code></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    courses_tab, modules_tab = st.tabs(["Programme Rankings", "Module Matches"])

    with courses_tab:
        render_course_cards(top_courses)
        st.markdown('<div class="section-label">Full ranking</div>', unsafe_allow_html=True)
        render_course_table(top_courses)

    with modules_tab:
        render_module_cards(top_modules)


def render_chat_evidence(sources: List[Dict[str, Any]], top_courses: List[Dict[str, Any]]) -> None:
    if top_courses:
        st.caption("Top programmes considered")
        for course in top_courses[:3]:
            st.markdown(
                f"- `{escape(str(course.get('school', '')))}:` {escape(str(course.get('course', '')))} ({format_pct(course.get('score', 0))})"
            )

    if sources:
        st.caption("Grounded in these modules")
        for source in sources:
            label = f"{source.get('code', '')} - {source.get('title', '')}"
            meta = f"{source.get('school', '')} - {source.get('course', '')}"
            st.markdown(f"- `{escape(label)}` - {escape(meta)}")


def render_matcher_tab(api_base: str, demo_mode: bool, top_n: int) -> None:
    st.subheader("Job Advertisement")
    with st.form("job_match_form"):
        job_title = st.text_input("Job Title", placeholder="e.g. Data Scientist")
        job_text = st.text_area(
            "Job Description",
            height=240,
            placeholder="Paste the full job description here...",
        )
        submitted = st.form_submit_button("Find Matching Courses", type="primary", use_container_width=True)

    if submitted:
        st.session_state["last_error"] = None

        if demo_mode:
            st.session_state["result"] = DEMO_RESULT
            st.session_state["result_source"] = "Demo"
        elif not job_text.strip():
            st.session_state["last_error"] = "Please paste a job description before running the matcher."
        else:
            try:
                with st.spinner("Scoring the job description against the module embeddings..."):
                    result = fetch_matches(api_base, job_title.strip(), job_text.strip(), top_n)
                st.session_state["result"] = result
                st.session_state["result_source"] = "Live backend"
            except requests.HTTPError as exc:
                message = exc.response.text if exc.response is not None else str(exc)
                st.session_state["last_error"] = f"Backend request failed: {message}"
            except requests.RequestException as exc:
                st.session_state["last_error"] = f"Could not reach the backend at `{api_base}`. Details: {exc}"

    if st.session_state["last_error"]:
        st.error(st.session_state["last_error"])

    if st.session_state["result"]:
        render_result(
            st.session_state["result"],
            api_base=api_base,
            source_label=st.session_state.get("result_source", "Unknown"),
        )


def render_chatbot_tab(api_base: str, health: Optional[Dict[str, Any]]) -> None:
    st.subheader("Grounded Chatbot")
    st.markdown(
        """
        <div class="empty-state">
          <strong>Ask follow-up questions about the retrieved course data</strong>
          The chatbot retrieves relevant modules and programmes first, then asks the LLM to answer from that context instead of free-styling.
        </div>
        """,
        unsafe_allow_html=True,
    )

    controls = st.columns([1.0, 0.42, 2.58], gap="medium")
    with controls[0]:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state["chat_history"] = []
            st.session_state["chat_last_error"] = None
            st.rerun()
    with controls[2]:
        model_label = "Unavailable"
        if health and health.get("llm_configured"):
            model_label = str(health.get("llm_model", "Configured"))
        st.markdown(
            f'<div class="chat-toolbar-meta">Backend target: <code>{escape(api_base)}</code> | Chat model: {escape(model_label)}</div>',
            unsafe_allow_html=True,
        )

    if health is None:
        st.warning("Backend is not reachable yet. Start the backend before using the chatbot tab.")
        return

    if not health.get("llm_configured"):
        st.warning(
            "The backend does not have an LLM key configured yet. Add `GEMINI_API_KEY` or `OPENAI_API_KEY` to `llm_app/.env`, then restart the backend."
        )
        return

    if not st.session_state["chat_history"]:
        st.markdown('<div class="section-label">Suggested prompts</div>', unsafe_allow_html=True)
        for suggestion in CHAT_SUGGESTIONS:
            st.markdown(f"- {suggestion}")

    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            render_chat_evidence(message.get("sources", []), message.get("top_courses", []))

    prompt = st.chat_input("Ask about course fit, module evidence, or cross-school comparisons...")
    if not prompt:
        return

    st.session_state["chat_last_error"] = None
    st.session_state["chat_history"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    history_for_request = st.session_state["chat_history"][:-1]

    try:
        with st.chat_message("assistant"):
            with st.spinner("Grounding your question in the module data..."):
                result = fetch_chat(api_base, prompt, history_for_request)
            st.markdown(result["answer"])
            render_chat_evidence(result.get("sources", []), result.get("top_courses", []))
        st.session_state["chat_history"].append(
            {
                "role": "assistant",
                "content": result["answer"],
                "sources": result.get("sources", []),
                "top_courses": result.get("top_courses", []),
            }
        )
    except requests.HTTPError as exc:
        message = exc.response.text if exc.response is not None else str(exc)
        if exc.response is not None:
            try:
                payload = exc.response.json()
                message = payload.get("detail", message)
            except ValueError:
                pass
        if exc.response is not None and exc.response.status_code == 503:
            st.session_state["chat_last_error"] = message
        else:
            st.session_state["chat_last_error"] = f"Backend request failed: {message}"
    except requests.RequestException as exc:
        st.session_state["chat_last_error"] = f"Could not reach the backend at `{api_base}`. Details: {exc}"

    if st.session_state["chat_last_error"]:
        st.error(st.session_state["chat_last_error"])


def main() -> None:
    init_state()
    st.set_page_config(page_title="Course-Career Alignment Tool", page_icon="M", layout="wide")
    logo_data_uri = load_logo_data_uri(MOE_LOGO_PATH)

    st.markdown(
        """
        <style>
        :root {
            --bg: #f5f8fe;
            --panel: rgba(255, 255, 255, 0.96);
            --panel-solid: #ffffff;
            --border: rgba(46, 71, 120, 0.12);
            --text: #24345b;
            --muted: #667694;
            --accent: #2563d8;
            --accent-strong: #3d82ff;
            --shadow: 0 22px 44px rgba(44, 68, 110, 0.12);
        }
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(37, 99, 216, 0.10), transparent 22%),
                radial-gradient(circle at left top, rgba(245, 200, 76, 0.18), transparent 26%),
                linear-gradient(180deg, #f7faff 0%, #eef3fb 100%);
            color: var(--text);
        }
        .hero {
            background:
                radial-gradient(circle at top right, rgba(61, 130, 255, 0.16), transparent 26%),
                linear-gradient(135deg, #ffffff 0%, #f7faff 48%, #eef4ff 100%);
            border-radius: 28px;
            padding: 1.9rem 2rem;
            color: var(--text);
            margin-bottom: 1.4rem;
            box-shadow: var(--shadow);
            border: 1px solid rgba(46, 71, 120, 0.10);
            position: relative;
            overflow: hidden;
        }
        .hero::before {
            content: "";
            position: absolute;
            inset: auto -8% -72% 28%;
            height: 16rem;
            background: radial-gradient(circle, rgba(245, 200, 76, 0.28) 0%, rgba(245, 200, 76, 0.08) 40%, transparent 72%);
            pointer-events: none;
        }
        .hero-grid {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 122px minmax(0, 1fr);
            gap: 1.35rem;
            align-items: center;
        }
        .hero-logo {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 122px;
            height: 122px;
        }
        .hero-logo img {
            width: 100%;
            max-width: 110px;
            height: auto;
            object-fit: contain;
            display: block;
        }
        .hero-copy {
            min-width: 0;
        }
        .hero h1 {
            font-size: 2.25rem;
            margin: 0 0 0.45rem 0;
            letter-spacing: -0.03em;
            color: #26385f;
        }
        .hero p {
            margin: 0;
            color: #5a6885;
            max-width: 50rem;
            line-height: 1.6;
        }
        .hero p code {
            background: #eef4ff;
            border: 1px solid rgba(37, 99, 216, 0.10);
            color: #36548b;
            border-radius: 8px;
            padding: 0.08rem 0.38rem;
            font-size: 0.95em;
        }
        .eyebrow {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #e9f1ff;
            border: 1px solid rgba(37, 99, 216, 0.10);
            color: var(--accent);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.9rem;
            font-weight: 700;
        }
        .chat-toolbar-meta {
            color: var(--muted);
            font-size: 0.95rem;
            line-height: 1.6;
            padding-top: 0.62rem;
            margin-left: 1.4rem;
        }
        .chat-toolbar-meta code {
            background: #f3f7ff;
            border: 1px solid var(--border);
            color: #36548b;
            border-radius: 8px;
            padding: 0.1rem 0.4rem;
        }
        .job-summary {
            background: var(--panel-solid);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1rem 1.1rem;
            margin: 0.75rem 0 1rem 0;
            box-shadow: var(--shadow);
        }
        .job-summary .label {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
        }
        .job-summary .title {
            font-size: 1.2rem;
            font-weight: 700;
            margin-top: 0.35rem;
            color: var(--text);
        }
        .result-meta {
            margin: 0.2rem 0 1rem 0;
            color: var(--muted);
            font-size: 0.9rem;
        }
        .result-meta code {
            background: #f3f7ff;
            border: 1px solid var(--border);
            color: #36548b;
            border-radius: 8px;
            padding: 0.15rem 0.45rem;
        }
        .section-label {
            margin: 1.1rem 0 0.65rem 0;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--muted);
            font-weight: 700;
        }
        .course-card, .module-card, .summary-card, .empty-state {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            box-shadow: var(--shadow);
        }
        .course-card {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .course-card h3 {
            margin: 0.75rem 0 0.8rem 0;
            font-size: 1.08rem;
            line-height: 1.35;
            color: var(--text);
        }
        .course-topline {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.7rem;
            flex-wrap: wrap;
        }
        .school-pill, .rank-pill, .module-code, .module-school, .module-score, .table-school-pill {
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 999px;
            font-size: 0.74rem;
            font-weight: 700;
        }
        .rank-pill {
            background: rgba(245, 200, 76, 0.22);
            color: #8a6500;
        }
        .course-metrics {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem;
            margin-bottom: 0.85rem;
        }
        .metric-label {
            color: var(--muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.2rem;
        }
        .metric-value {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text);
        }
        .score-bar {
            height: 0.55rem;
            background: #e7eefb;
            border-radius: 999px;
            overflow: hidden;
        }
        .score-bar span {
            display: block;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--accent) 0%, var(--accent-strong) 100%);
        }
        .best-module {
            margin-top: 0.85rem;
            color: #4d5d7a;
            font-size: 0.9rem;
        }
        .best-module span {
            display: block;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            font-size: 0.72rem;
            margin-bottom: 0.2rem;
        }
        .summary-card {
            padding: 1rem 1rem 0.9rem 1rem;
            margin-bottom: 0.8rem;
        }
        .summary-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--muted);
            margin-bottom: 0.45rem;
        }
        .summary-value {
            color: var(--text);
            font-size: 1.35rem;
            font-weight: 700;
        }
        .ranking-table-wrap {
            overflow-x: auto;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 18px;
            box-shadow: var(--shadow);
        }
        .ranking-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 760px;
        }
        .ranking-table th {
            text-align: left;
            padding: 0.95rem 1rem;
            font-size: 0.76rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #6f809e;
            background: #f3f7ff;
            border-bottom: 1px solid var(--border);
        }
        .ranking-table td {
            padding: 0.95rem 1rem;
            color: #314468;
            border-bottom: 1px solid rgba(46, 71, 120, 0.08);
            vertical-align: top;
        }
        .ranking-table tr:last-child td {
            border-bottom: none;
        }
        .module-card {
            padding: 1rem;
            margin-bottom: 1rem;
            min-height: 220px;
        }
        .module-meta {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            margin-bottom: 0.6rem;
            flex-wrap: wrap;
        }
        .module-code {
            background: rgba(37, 99, 216, 0.10);
            color: #2454ab;
        }
        .module-school {
            border: 1px solid rgba(46, 71, 120, 0.08);
        }
        .module-course {
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--muted);
            font-size: 0.78rem;
            margin-bottom: 0.65rem;
        }
        .module-card h4 {
            margin: 0 0 0.45rem 0;
            font-size: 1rem;
            color: var(--text);
        }
        .module-card p {
            color: #5a6885;
            line-height: 1.55;
            font-size: 0.92rem;
        }
        .module-score {
            margin-top: 0.9rem;
        }
        .empty-state {
            border-style: dashed;
            padding: 1.2rem 1.25rem;
            color: #5d6d8a;
        }
        .empty-state strong {
            display: block;
            font-size: 1rem;
            margin-bottom: 0.3rem;
            color: var(--text);
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #f4f8ff 100%);
            border-right: 1px solid var(--border);
        }
        section[data-testid="stSidebar"] * {
            color: var(--text);
        }
        section[data-testid="stSidebar"] .stCaption {
            color: var(--muted) !important;
        }
        .stTextInput label, .stTextArea label, .stSlider label {
            color: var(--text) !important;
            font-weight: 600;
        }
        .stTextInput > div > div,
        .stTextArea > div > div,
        .stNumberInput > div > div,
        div[data-baseweb="base-input"],
        div[data-baseweb="base-input"] > div,
        div[data-baseweb="select"] > div,
        div[data-testid="stChatInput"] > div {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            border-radius: 14px !important;
            box-shadow: 0 8px 18px rgba(44, 68, 110, 0.05) !important;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="textarea"] {
            background: #ffffff !important;
            border: 1px solid var(--border) !important;
            border-radius: 14px !important;
            box-shadow: 0 8px 18px rgba(44, 68, 110, 0.05);
        }
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        div[data-baseweb="base-input"] input,
        div[data-baseweb="textarea"] textarea,
        div[data-testid="stChatInput"] textarea,
        div[data-testid="stChatInput"] input {
            color: var(--text) !important;
            background: #ffffff !important;
            -webkit-text-fill-color: var(--text) !important;
        }
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder,
        .stNumberInput input::placeholder,
        div[data-baseweb="base-input"] input::placeholder,
        div[data-baseweb="textarea"] textarea::placeholder,
        div[data-testid="stChatInput"] textarea::placeholder,
        div[data-testid="stChatInput"] input::placeholder {
            color: #8a98b2 !important;
            -webkit-text-fill-color: #8a98b2 !important;
        }
        div[data-baseweb="input"] input,
        div[data-baseweb="textarea"] textarea {
            color: var(--text) !important;
            background: transparent !important;
        }
        div[data-testid="stChatInput"] button {
            color: var(--accent) !important;
        }
        button[kind="primary"] {
            background: linear-gradient(135deg, var(--accent) 0%, var(--accent-strong) 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
        }
        button[data-baseweb="tab"] {
            color: #64738f !important;
            font-weight: 700 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--accent) !important;
        }
        div[data-testid="stChatMessage"] {
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid var(--border);
            border-radius: 18px;
            box-shadow: 0 14px 30px rgba(44, 68, 110, 0.07);
        }
        @media (max-width: 820px) {
            .hero {
                padding: 1.35rem 1.2rem;
            }
            .hero-grid {
                grid-template-columns: 1fr;
                text-align: left;
            }
            .hero-logo {
                width: 94px;
                height: 94px;
            }
            .hero-logo img {
                max-width: 84px;
            }
            .hero h1 {
                font-size: 1.75rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    logo_html = ""
    if logo_data_uri:
        logo_html = f'<div class="hero-logo"><img src="{logo_data_uri}" alt="Ministry of Education Singapore logo" /></div>'

    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-grid">
            {logo_html}
            <div class="hero-copy">
              <div class="eyebrow">MOE Higher Education Group</div>
              <h1>Uni2Work SG</h1>
              <p>A tool for MOE officers to assess how well university courses prepare students for real-world jobs through skill alignment analysis.</p>
              <p style="margin-top:0.8rem;">Use <code>Course Matcher</code> by pasting a job description to identify the most relevant degree programmes and modules or switch to <code>LLM Chatbot</code> to ask follow-up questions about the retrieved course data.</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Configuration")
        api_base = st.text_input("Backend API URL", DEFAULT_BACKEND_URL).rstrip("/")
        top_n = st.slider("Top programmes", min_value=5, max_value=15, value=10)
        demo_mode = st.toggle("Use demo data for matcher", value=False)
        health = fetch_health(api_base)
        if health:
            st.caption(f"Modules loaded: {health.get('modules_loaded', 0)}")
            if health.get("llm_configured"):
                st.caption(f"Chatbot model: {health.get('llm_model', 'Configured')}")
            else:
                st.caption("Chatbot LLM not configured yet.")
        else:
            st.caption("Backend health unavailable.")
        st.caption("When running with Docker Compose, use `http://backend:8000` inside the container.")

    matcher_tab, chatbot_tab = st.tabs(["Course Matcher", "LLM Chatbot"])

    with matcher_tab:
        render_matcher_tab(api_base, demo_mode, top_n)

    with chatbot_tab:
        render_chatbot_tab(api_base, health)


if __name__ == "__main__":
    main()
