"""Resume parsing and fit scoring for FirstJob Agent.

Uses Google's Gemini API (free tier via AI Studio). The key comes from the
GEMINI_API_KEY environment variable or, on Streamlit Cloud, st.secrets.
Every function degrades gracefully when no key is set.
"""
import json
import os
import re
import time

# Fallback model order, used only if live discovery through the API fails.
# Availability and free-tier quota vary by key and project, so the real list
# comes from the models endpoint at runtime (see _discover_models). Override
# with the GEMINI_MODEL environment variable (or a secret of the same name).
MODEL_CANDIDATES = ["gemini-2.5-flash", "gemini-2.5-flash-lite",
                    "gemini-2.0-flash", "gemini-3.6-flash",
                    "gemini-3.5-flash", "gemini-3.8-flash"]

# Model names that look like text generators but are not for this app.
_SKIP_MODELS = ("embedding", "imagen", "tts", "aqa", "nano", "robotics")


def _model_rank(name):
    """Lower sorts first: flash, then flash-lite, then other gemini, then rest;
    'latest' aliases ahead of dated versions inside each group."""
    n = name.lower()
    if "flash-lite" in n:
        group = 1
    elif "flash" in n:
        group = 0
    elif "gemini" in n:
        group = 2
    else:
        group = 3
    return (group, 0 if "latest" in n else 1, n)


def _discover_models(client):
    """Ask the API which models this key can actually use.

    Returns an ordered list of model names that support generateContent,
    or None if discovery failed. The result is cached for the process.
    """
    global _DISCOVERED
    if _DISCOVERED:
        return _DISCOVERED
    models = []
    try:
        for m in client.models.list():
            name = (getattr(m, "name", "") or "").split("/")[-1]
            actions = (getattr(m, "supported_actions", None)
                       or getattr(m, "supported_generation_methods", None) or [])
            if "generateContent" not in actions:
                continue
            if any(bad in name.lower() for bad in _SKIP_MODELS):
                continue
            models.append(name)
    except Exception:
        return None
    if not models:
        return None
    models.sort(key=_model_rank)
    _DISCOVERED = models
    return models

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
# Name of the model that answered the most recent successful call.
LAST_MODEL = None
# The model known to work with this key; tried first on later calls.
WORKING_MODEL = None
# Cached result of model discovery for this process.
_DISCOVERED = None


def _attempt_chain(client, models, prompt, config, errors):
    """Try each model in order. Returns the reply text, or None if all fail;
    appends "model: error" strings to errors."""
    global LAST_ERROR, LAST_MODEL, WORKING_MODEL
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
                LAST_MODEL = model
                WORKING_MODEL = model
                return response.text
            except Exception as exc:
                errors.append(f"{model}: {exc}")
                msg = str(exc)
                # 404/429/quota/auth errors are about the model or key, not
                # the config - move straight to the next model.
                if ("404" in msg or "429" in msg or "NOT_FOUND" in msg
                        or "RESOURCE_EXHAUSTED" in msg or "API key" in msg
                        or "quota" in msg.lower()):
                    break
                continue
    return None


def ask_gemini(prompt, max_output_tokens=None):
    """Send one prompt to Gemini. Returns the reply text, or None if no key.

    If every model fails with a short-lived rate limit (429), waits 20s and
    retries the chain once - free-tier per-minute limits clear that fast.
    Daily-quota errors are not retried.
    """
    global LAST_ERROR
    client = get_client()
    if client is None:
        return None
    override = os.environ.get("GEMINI_MODEL")
    if override:
        models = [override]
    else:
        # The last working model goes first; behind it, the live-discovered
        # list for this key, or the hardcoded candidates if discovery failed.
        discovered = _discover_models(client) or MODEL_CANDIDATES
        models = ([WORKING_MODEL] if WORKING_MODEL else []) \
            + [m for m in discovered if m != WORKING_MODEL]
    config = _make_config(max_output_tokens)
    errors = []
    text = _attempt_chain(client, models, prompt, config, errors)
    if (text is None and errors
            and any("429" in e or "RESOURCE_EXHAUSTED" in e
                    or "quota" in e.lower() for e in errors)
            and not any("day" in e.lower() for e in errors)):
        time.sleep(20)
        text = _attempt_chain(client, models, prompt, config, errors)
    if text is None:
        LAST_ERROR = "; ".join(e[:160] for e in errors)[:300]
    return text


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
    n = len(skills)
    return {
        "skills": skills,
        "education": "",
        "projects": [],
        "search_keywords": keywords[:3],
        "summary": "",
        "skills_to_learn": [],
        "level": "beginner" if n <= 6 else "intermediate" if n <= 12 else "advanced",
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
                "skills_to_learn": [], "level": "", "source": "none"}

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
- "level": the student's experience level - "beginner" (mostly coursework), "intermediate" (some solid projects), or "advanced" (deep or many projects, or prior internships)
- "skills_to_learn": the 2 skills that would most increase their internship matches in the chosen role areas and are NOT already in the resume"""
    data = ask_gemini_json(prompt, max_output_tokens=600)
    if not isinstance(data, dict) or not data.get("search_keywords"):
        return heuristic_analysis(resume_text, role_areas)
    data["source"] = "gemini"
    return data


_ENTRY_TERMS = ("intern", "trainee", "fresher", "junior", "entry level",
                "entry-level", "graduate")
_SENIOR_TERMS = ("senior", "lead", "manager", "head of", "principal",
                 "staff engineer")


def _overlap_score(student_skills, text, level=""):
    """Crude fit score 0-100 from shared skill words (fallback path).

    Level-aware: entry-level postings suit beginners, senior-titled ones
    suit them less (and the reverse, mildly, for advanced students).
    """
    lower = (text or "").lower()
    words = set(re.findall(r"[a-z+#]+", lower))
    hits = sum(1 for s in student_skills if any(tok in words for tok in s.lower().split()))
    score = min(95, 30 + hits * 15) if hits else 25
    if level == "beginner":
        if any(t in lower for t in _ENTRY_TERMS):
            score += 10
        if any(t in lower for t in _SENIOR_TERMS):
            score -= 15
    elif level == "advanced" and any(t in lower for t in _SENIOR_TERMS):
        score += 5
    return score


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
            score = _overlap_score(skills, basis, analysis.get("level") or "")
            if not reason:
                matched = [s for s in skills if s.lower().split()[0] in basis.lower()]
                reason = ("Matches your " + ", ".join(matched[:3])) if matched else "Different area from your main skills"
        item["fit_score"] = max(0, min(100, score))
        item["fit_reason"] = reason
    return items
