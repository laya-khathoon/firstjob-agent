"""FirstJob Agent - find internships you actually qualify for.

Upload a resume (or paste the text), answer 3 quick questions, and get real,
currently open internships with a fit score, working apply links, and a
drafted application message. Listings come from the sites themselves and are
never invented by the AI. Nothing is stored; everything stays in session state.

Run with:  python -m streamlit run app.py
"""
import streamlit as st

from application_drafter import draft_application
from internship_searcher import search_internships
from resume_parser import (analyze_resume, extract_pdf_text, get_api_key,
                           score_fit)

st.set_page_config(page_title="FirstJob Agent", page_icon="🎯", layout="centered")

ROLE_AREAS = ["AI/ML", "web development", "data", "cybersecurity", "other"]


def fit_badge(score):
    """Colored fit badge as a small HTML span. Missing scores render nothing."""
    if score is None:
        return ""
    color = "#1a7f37" if score >= 70 else "#9a6700" if score >= 40 else "#57606a"
    return (f'<span style="background:{color};color:#fff;padding:2px 10px;'
            f'border-radius:12px;font-size:0.85em;white-space:nowrap">'
            f'Fit {score}/100</span>')


def show_match_card(index, match, analysis):
    """Render one match card. Every field uses .get() so a missing key (for
    example 'company') can never crash the page."""
    title = match.get("title") or "Internship"
    company = match.get("company") or ""
    site = match.get("site") or ""
    heading = title + (f" · {company}" if company else "")

    with st.container(border=True):
        head = f"**{heading}**"
        if site:
            head += f"  \n{site}"
        st.markdown(f"{head} &nbsp; {fit_badge(match.get('fit_score'))}",
                    unsafe_allow_html=True)

        details = []
        if match.get("location"):
            details.append(f"📍 {match['location']}")
        if match.get("stipend"):
            details.append(f"💰 {match['stipend']}")
        if details:
            st.caption(" · ".join(details))

        skills = match.get("skills") or []
        if skills:
            st.caption("Skills asked: " + ", ".join(skills[:8]))

        if match.get("fit_reason"):
            st.write(match["fit_reason"])

        url = match.get("url") or ""
        col1, col2 = st.columns([1, 1])
        with col1:
            if url:
                st.link_button("Open posting", url, type="primary")
        with col2:
            if st.button("Draft my application", key=f"draft_btn_{index}"):
                if not get_api_key():
                    st.warning("Add your Gemini API key to draft applications.")
                else:
                    with st.spinner("Drafting from your resume..."):
                        st.session_state[f"draft_{index}"] = (
                            draft_application(analysis, match)
                            or "Drafting failed. Try again.")
        if st.session_state.get(f"draft_{index}"):
            st.text_area("Your draft - read it and edit before sending:",
                         value=st.session_state[f"draft_{index}"],
                         height=180, key=f"draft_text_{index}")


def show_page_card(page):
    """A live search page on a board we could not parse automatically."""
    keyword = page.get("keyword") or "internships"
    site = page.get("site") or "job board"
    with st.container(border=True):
        st.markdown(f"**Browse “{keyword}” internships on {site}** &nbsp; "
                    f"{fit_badge(page.get('fit_score'))}", unsafe_allow_html=True)
        if page.get("fit_reason"):
            st.write(page["fit_reason"])
        st.caption("Live search page on the site itself - every listing you see there is current.")
        if page.get("url"):
            st.link_button(f"Open {site}", page["url"])


def main():
    st.title("🎯 FirstJob Agent")
    st.caption("Find internships you actually qualify for. Real links only - "
               "the AI never invents a listing.")

    if not get_api_key():
        st.warning("No Gemini API key found, so resume analysis and drafting are off. "
                   "Set GEMINI_API_KEY (or add it in Streamlit Secrets) to switch them on. "
                   "You can still browse live internship searches below.")

    # --- 1. Resume input -------------------------------------------------
    st.subheader("1. Your resume")
    resume_text = ""
    uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    if uploaded is not None:
        try:
            resume_text = extract_pdf_text(uploaded)
            st.success("Resume read.")
        except ValueError as exc:
            st.error(str(exc))
    pasted = st.text_area("...or paste your resume text", height=150,
                          placeholder="Paste the text of your resume here")
    if pasted.strip():
        resume_text = pasted

    # --- 2. Three questions ----------------------------------------------
    st.subheader("2. Three quick questions")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        role_areas = st.multiselect("Role areas", ROLE_AREAS,
                                    default=["AI/ML"])
    with col_b:
        work_mode = st.selectbox("Work mode", ["Both", "Remote", "On-site"])
    with col_c:
        stipend_required = st.checkbox("Stipend required")

    # --- 3. Search ---------------------------------------------------------
    st.subheader("3. Your matches")
    if st.button("Find Matching Internships", type="primary"):
        with st.spinner("Reading your resume..."):
            analysis = analyze_resume(resume_text, role_areas, work_mode,
                                      stipend_required)
        st.session_state["analysis"] = analysis
        status = st.empty()
        with st.spinner("Searching live internship boards..."):
            results = search_internships(
                analysis.get("search_keywords"),
                progress=lambda msg: status.caption(msg))
        status.empty()
        preferences = (f"The student prefers {work_mode.lower()} work"
                       + (" and needs a stipend." if stipend_required else "."))
        score_fit(analysis, results.get("live") or [], preferences)
        score_fit(analysis, results.get("pages") or [], preferences)
        st.session_state["results"] = results
        st.session_state.pop("_drafts_cleared", None)
        for key in [k for k in st.session_state if k.startswith("draft_")]:
            del st.session_state[key]

    analysis = st.session_state.get("analysis") or {}
    results = st.session_state.get("results")

    if results is not None:
        live = results.get("live") or []
        pages = results.get("pages") or []

        if not live and not pages:
            st.info("Nothing came through from the internship sites just now. "
                    "Try again in a few minutes.")
            to_learn = analysis.get("skills_to_learn") or []
            if to_learn:
                st.write("The 2 skills that would unlock the most matches for you: "
                         f"**{', '.join(to_learn[:2])}**")
        else:
            if live:
                st.markdown(f"### Found live just now ({len(live)})")
                for i, match in enumerate(live):
                    show_match_card(i, match, analysis)
            if pages:
                st.markdown("### Live searches on the big boards")
                for page in pages:
                    show_page_card(page)

        st.divider()
        st.caption("Every link above was fetched or checked just now. If a posting "
                   "was filled between our check and your click, the site will say so.")

    st.divider()
    st.caption("Built for Code for a Billion 2026 · Your resume is never stored - "
               "it stays in this browser session only.")


if __name__ == "__main__":
    main()
