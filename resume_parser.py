"""Resume parsing and fit scoring for FirstJob Agent.

Uses Google's Gemini API (free tier via AI Studio). The key comes from the
GEMINI_API_KEY environment variable or, on Streamlit Cloud, st.secrets.
Every function degrades gracefully when no key is set.
"""
import json
import os
import re

# Models tried in order. gemini-3.8-flash (the newest free-tier Flash) was
# returning 503 "high demand" at build time and the SDK retries it for minutes,
# so the default order starts with the fastest reliable one. Override with the
# GEMINI_MODEL environment variable (or a Streamlit secret of the same name).
MODEL_CANDIDATES = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.8-flash"]

# Skills we can spot without an LLM (fallback path).
KNOWN_SKILLS = [
    "python", "java", "c", "c++", "javascript", "typescript", "sql", "html", "css",
    "react", "node", "flask", "django", "fastapi", "streamlit", "pandas", "numpy",
    "scikit-learn", "tensorflow", "pytorch", "keras", "machine learning",
    "deep learning", "data analysis", "data science", "nlp", "computer vision",
    "git", "github", "rest api", "mongodb", "mysql", "postgresql", "docker",
    "linux", "excel", "power bi", "tableau", "cyber security", "networking",
    "prompt engineering", "llm", "rag", "aws", "gcp", "azure",
]

ROLE_AREA_KEYWORDS = {
    "AI/ML": ["machine learning", "artificial intelligence", "data science"],
    "web development": ["web development", "python", "react"],
    "data": ["data analyst", "data science", "sql"],
    "cybersecurity": ["cyber security", "ethical hacking"],
    "other": [],
}


def get_api_key():
    """Return the Gemini API key from env or Streamlit secrets, or None."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def get_client():
    key = get_api_key()
    if not key:
        return None
    from google import genai
    try:
        from google.genai import types
        http_options = types.HttpOptions(timeout=30000)
        return genai.Client(api_key=key, http_options=http_options)
    except Exception:
        return genai.Client(api_key=key)


def _make_config(max_output_tokens):
    """Fast-generation config: capped output, thinking off. None if unsupported."""
    try:
        from google.genai import types
        kwargs = {}
        if max_output_tokens:
            kwargs["max_output_tokens"] = max_output_tokens
        try:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        except Exception:
            pass
        return types.GenerateContentConfig(**kwargs) if kwargs else None
    except Exception:
        return None


# Short description of the most recent Gemini failure (for the UI to show).
# None means the last call worked, or no call has been made yet.
LAST_ERROR = None


def ask_gemini(prompt, max_output_tokens=None):
    """Send one prompt to Gemini. Returns the reply text, or None if no key."""
    global LAST_ERROR
    client = get_client()
    if client is None:
        return None
    override = os.environ.get("GEMINI_MODEL")
    models = [override] if override else MODEL_CANDIDATES
    config = _make_config(max_output_tokens)
    errors = []
    for model in models:
        # Try the fast config first; if this SDK/model rejects it, retry plain.
        for cfg in (config, None):
            try:
                if cfg is not None:
                    response = client.models.generate_content(
                        model=model, contents=prompt, config=cfg)
                else:
                    response = client.models.generate_content(
                        model=model, contents=prompt)
                LAST_ERROR = None
                return response.text
            except Exception as exc:
                errors.append(f"{model}: {exc}")
                continue
    LAST_ERROR = "; ".join(e[:160] for e in errors)[:300]
    return None


def ask_gemini_json(prompt, max_output_tokens=None):
    """Ask Gemini for JSON and parse it tolerantly. Returns None on failure."""
    text = ask_gemini(prompt + "\n\nReply with JSON only. No markdown fences, no commentary.",
                      max_output_tokens=max_output_tokens)
    if not text:
        return None
    match = re.search(r"[\{\[].*[\}\]]", text, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def extract_pdf_text(uploaded_file):
    """Extract text from an uploaded PDF. Raises ValueError with a friendly message."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(uploaded_file)
        parts = [(page.extract_text() or "") for page in reader.pages]
        text = "\n".join(parts).strip()
        if not text:
            raise ValueError("No readable text found in that PDF. Try pasting the text instead.")
        return text
    except ValueError:
        raise
    except Exception:
        raise ValueError("That PDF could not be read. Try a different file or paste the text instead.")


def heuristic_analysis(resume_text, role_areas):
    """Instant keyword-scan analysis. Used as the Gemini fallback and to pick
    the search keywords up front so the live search can start immediately,
    in parallel with the slower Gemini analysis."""
    lower = resume_text.lower()
    skills = [s for s in KNOWN_SKILLS if s in lower]
    keywords = []
    for area in role_areas or []:
        for kw in ROLE_AREA_KEYWORDS.get(area, []):
            if kw not in keywords:
                keywords.append(kw)
    if not keywords:
        keywords = skills[:3]
    return {
        "skills": skills,
        "education": "",
        "projects": [],
        "search_keywords": keywords[:3],
        "summary": "",
        "skills_to_learn": [],
        "source": "fallback",
    }


def analyze_resume(resume_text, role_areas, work_mode, stipend_required):
    """Extract skills, education, projects and 2-3 search keywords from a resume.

    Returns a dict; never raises. Uses Gemini when a key is set, otherwise a
    simple keyword scan so the app still works for browsing.
    """
    if not resume_text or not resume_text.strip():
        return {"skills": [], "education": "", "projects": [],
                "search_keywords": [], "summary": "",
                "skills_to_learn": [], "source": "none"}

    prompt = f"""You are reading a student's resume to help them find internships.

Resume text:
\"\"\"
{resume_text[:3500]}
\"\"\"

The student is interested in these role areas: {', '.join(role_areas or ['any'])}.
Work mode preference: {work_mode}. Stipend required: {'yes' if stipend_required else 'no'}.

Return a JSON object with exactly these keys:
- "skills": list of the student's real skills (strings, only ones stated in the resume)
- "education": one line on their education
- "projects": list of short project descriptions (strings)
- "search_keywords": the 2 or 3 best internship search keywords for this student. Each must be a simple, common role or skill term that internship sites use (examples: "machine learning", "python", "web development", "data analyst", "cyber security"). Prefer their strongest skills inside the chosen role areas.
- "summary": one sentence about the student
- "skills_to_learn": the 2 skills that would most increase their internship matches in the chosen role areas and are NOT already in the resume"""
    data = ask_gemini_json(prompt, max_output_tokens=600)
    if not isinstance(data, dict) or not data.get("search_keywords"):
        return heuristic_analysis(resume_text, role_areas)
    data["source"] = "gemini"
    return data


def _overlap_score(student_skills, text):
    """Crude fit score 0-100 from shared skill words (fallback path)."""
    words = set(re.findall(r"[a-z+#]+", (text or "").lower()))
    hits = sum(1 for s in student_skills if any(tok in words for tok in s.lower().split()))
    return min(95, 30 + hits * 15) if hits else 25


def score_fit(analysis, items, preferences="", use_gemini=True):
    """Add 'fit_score' (0-100) and 'fit_reason' to each item dict, in place.

    items: list of dicts with at least a title; may have company, skills etc.
    One batched Gemini call when possible; overlap heuristic otherwise.
    use_gemini=False forces the instant local overlap score (used for the
    board search-page cards, where a Gemini call adds little).
    Every field is written with .get-style safety: missing input keys are fine.
    """
    skills = analysis.get("skills") or []
    if not items:
        return items
    prompt = f"""Student skills: {', '.join(skills) or 'not stated'}.
{preferences}
Score how well each internship below fits this student, 0-100, and give one short line on why it fits or the main missing skill.

Internships:
{json.dumps([{k: it.get(k) for k in ('title', 'company', 'skills', 'keyword')} for it in items], ensure_ascii=False)}

Return a JSON list, same order, one object per internship: {{"score": <int>, "reason": "<one short line>"}}"""
    scores = (ask_gemini_json(prompt, max_output_tokens=1500)
              if use_gemini and (skills or any(it.get("skills") for it in items))
              else None)
    for i, item in enumerate(items):
        score, reason = None, ""
        if isinstance(scores, list) and i < len(scores) and isinstance(scores[i], dict):
            raw = scores[i].get("score")
            if isinstance(raw, (int, float)):
                score = int(raw)
            reason = str(scores[i].get("reason") or "")
        if score is None:
            basis = " ".join(str(item.get(k) or "") for k in ("title", "company", "keyword")) + " " + " ".join(item.get("skills") or [])
            score = _overlap_score(skills, basis)
            if not reason:
                matched = [s for s in skills if s.lower().split()[0] in basis.lower()]
                reason = ("Matches your " + ", ".join(matched[:3])) if matched else "Different area from your main skills"
        item["fit_score"] = max(0, min(100, score))
        item["fit_reason"] = reason
    return items
