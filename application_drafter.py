"""Draft a short, honest application message for one chosen internship."""
from resume_parser import ask_gemini


def draft_application(analysis, match):
    """Return a ~120-word application message, or None if Gemini is unavailable.

    Only facts from the student's own resume analysis may be used.
    """
    skills = ", ".join(analysis.get("skills") or []) or "not stated"
    projects = "; ".join(analysis.get("projects") or []) or "not stated"
    title = match.get("title") or "this internship"
    company = match.get("company") or "your organisation"

    prompt = f"""Draft a short internship application message (about 120 words) from a student.

The internship: {title} at {company}.
The student's real skills: {skills}.
The student's education: {analysis.get('education') or 'final-year BTech student'}.
The student's projects: {projects}.

Rules:
- Use ONLY the skills and projects listed above. Never invent or exaggerate.
- Plain, warm, professional tone. No buzzwords.
- One short paragraph on why they fit, one on what they want to learn, one line closing.
- Output the message text only, no subject line, no commentary."""
    return ask_gemini(prompt)
