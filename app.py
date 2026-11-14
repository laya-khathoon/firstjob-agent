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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;600&display=swap');
body, p, h1, h2, h3, h4, h5, h6, span, label, button, a, input,
textarea, li, summary, div {
    font-family: 'Raleway', 'Source Sans Pro', sans-serif; }
.fja-hero { animation: fja-fade 0.5s ease both; }
.fja-hero h1 { font-size: 2.2rem; letter-spacing: -0.02em;
               margin-bottom: 0.1rem; }
.fja-hero p { color: #aab1d4; font-size: 1.02rem; margin-top: 0; }
.fja-chip { display: inline-block; background: #424769; color: #e6e9f7;
            border: 1px solid #676f9d; border-radius: 4px;
            padding: 1px 8px; margin: 2px 4px 2px 0; font-size: 0.78rem; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 6px; animation: fja-rise 0.45s ease both; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(1) { animation-delay: 0.02s; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(2) { animation-delay: 0.06s; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(3) { animation-delay: 0.10s; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(4) { animation-delay: 0.14s; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(5) { animation-delay: 0.18s; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(6) { animation-delay: 0.22s; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(7) { animation-delay: 0.26s; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(8) { animation-delay: 0.30s; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(9) { animation-delay: 0.34s; }
[data-testid="stTabs"] div[data-testid="stVerticalBlockBorderWrapper"]:nth-of-type(10) { animation-delay: 0.38s; }
[data-testid="stMetric"] { animation: fja-rise 0.4s ease both; }
.stButton button, .stLinkButton a {
    transition: background-color 0.18s ease, border-color 0.18s ease,
                color 0.18s ease; }
.fja-skel { background: #424769; border-radius: 6px; height: 14px;
            margin: 10px 0; animation: fja-pulse 1.2s ease-in-out infinite; }
@keyframes fja-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.45; } }
@keyframes fja-rise { from { opacity: 0; transform: translateY(10px); }
                      to { opacity: 1; transform: none; } }
@keyframes fja-fade { from { opacity: 0; } to { opacity: 1; } }
@media (prefers-reduced-motion: reduce) {
    * { animation: none !important; transition: none !important; } }
</style>
""", unsafe_allow_html=True)


def fit_badge(score):
    """Colored fit badge as a small HTML span. Missing scores render nothing."""
    if score is None:
        return ""
    if score >= 70:
        bg, fg = "#f9b17a", "#2d3250"
    elif score >= 40:
        bg, fg = "#676f9d", "#ffffff"
    else:
        bg, fg = "#424769", "#dfe2f2"
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:4px;font-size:0.8rem;white-space:nowrap">'
            f'Fit {score}/100</span>')


def skill_chips(skills):
    """Inline pill chips for a list of skills."""
    return " ".join(f'<span class="fja-chip">{s}</span>' for s in skills[:8])


def show_skeleton():
    """Grey pulsing placeholder bars shown while the live search runs."""
    for width in ("45%", "85%", "70%", "90%", "40%"):
        st.markdown(f'<div class="fja-skel" style="width:{width}"></div>',
                    unsafe_allow_html=True)


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
            details.append(match["location"])
        if match.get("stipend"):
            details.append(match["stipend"])
        if details:
            st.caption(" · ".join(details))

        skills = match.get("skills") or []
        if skills:
            st.markdown(skill_chips(skills), unsafe_allow_html=True)

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


def show_analysis(analysis):
    """Expandable summary of what the agent read from the resume."""
    with st.expander("What the agent understood from your resume"):
        if analysis.get("summary"):
            st.write(analysis["summary"])
        skills = analysis.get("skills") or []
        if skills:
            st.markdown("**Skills found:** " + skill_chips(skills),
                        unsafe_allow_html=True)
        if analysis.get("education"):
            st.caption(f"Education: {analysis['education']}")
        projects = analysis.get("projects") or []
        if projects:
            st.markdown("**Projects:**")
            for project in projects[:4]:
                st.markdown(f"- {project}")
        keywords = analysis.get("search_keywords") or []
        if keywords:
            st.caption("Searching live boards for: "
                       + " · ".join(f"**{k}**" for k in keywords))
        to_learn = analysis.get("skills_to_learn") or []
        if to_learn:
            st.write("The 2 skills that would unlock the most matches for you: "
                     f"**{', '.join(to_learn[:2])}**")


def main():
    st.markdown('<div class="fja-hero"><h1>FirstJob Agent</h1>'
                "<p>Find internships you actually qualify for. Every link is "
                "fetched from the sites themselves - the AI never invents a "
                "listing.</p></div>",
                unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### How it works")
        st.markdown("1. Upload or paste your resume\n"
                    "2. Answer 3 quick questions\n"
                    "3. Get real openings, fit scores and a ready-to-edit draft")
        st.divider()
        st.markdown("### Your 3 answers")
        role_areas = st.multiselect("Role areas", ROLE_AREAS, default=["AI/ML"])
        work_mode = st.selectbox("Work mode", ["Both", "Remote", "On-site"])
        stipend_required = st.checkbox("Stipend required")

    if not get_api_key():
        st.warning("No Gemini API key found, so resume analysis and drafting are off. "
                   "Set GEMINI_API_KEY (or add it in Streamlit Secrets) to switch them on. "
                   "You can still browse live internship searches below.")

    # --- 1. Resume input -------------------------------------------------
    st.subheader("1. Your resume")
    resume_text = ""
    up_col, paste_col = st.columns(2)
    with up_col:
        uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
        if uploaded is not None:
            try:
                resume_text = extract_pdf_text(uploaded)
                st.success("Resume read.")
            except ValueError as exc:
                st.error(str(exc))
    with paste_col:
        pasted = st.text_area("...or paste your resume text", height=150,
                              placeholder="Paste the text of your resume here")
        if pasted.strip():
            resume_text = pasted

    # --- 2. Search ---------------------------------------------------------
    st.subheader("2. Find my matches")
    st.caption("Your 3 answers live in the sidebar (tap the > arrow at the top "
               "left if it is hidden).")
    if st.button("Find Matching Internships", type="primary",
                 use_container_width=True):
        with st.spinner("Reading your resume..."):
            analysis = analyze_resume(resume_text, role_areas, work_mode,
                                      stipend_required)
        st.session_state["analysis"] = analysis
        skeleton = st.empty()
        status = st.empty()
        with skeleton.container():
            show_skeleton()
        results = search_internships(
            analysis.get("search_keywords"),
            progress=lambda msg: status.caption(msg))
        skeleton.empty()
        status.empty()
        preferences = (f"The student prefers {work_mode.lower()} work"
                       + (" and needs a stipend." if stipend_required else "."))
        score_fit(analysis, results.get("live") or [], preferences)
        score_fit(analysis, results.get("pages") or [], preferences)
        st.session_state["results"] = results
        st.session_state.pop("_drafts_cleared", None)
        for key in [k for k in st.session_state if k.startswith("draft_")]:
            del st.session_state[key]

    # --- 3. Results --------------------------------------------------------
    analysis = st.session_state.get("analysis") or {}
    results = st.session_state.get("results")

    if results is not None:
        live = results.get("live") or []
        pages = results.get("pages") or []
        unverified = results.get("unverified_pages") or []
        stats = results.get("stats") or {}

        if analysis.get("source") == "fallback" and get_api_key():
            st.caption("Gemini analysis did not respond, so keyword matching "
                       "is on. Listings are still real.")

        if not live and not pages:
            st.warning("No verified listings came through from the internship "
                       "sites just now.")
            kws = analysis.get("search_keywords") or []
            if kws:
                st.caption("Searched for: "
                           + " · ".join(f"**{k}**" for k in kws))
            st.caption(
                f"From this network: {stats.get('fetched', 0)} postings fetched, "
                f"{stats.get('live_ok', 0)} passed the link check, "
                f"{stats.get('boards_ok', 0)} of {stats.get('boards_total', 0)} "
                "boards reachable. If these are all zero, the internship sites "
                "are blocking this network - try the hosted demo link or a "
                "different network.")
            if unverified:
                st.write("These board search pages could not be verified from "
                         "this network, but they are the sites' own links:")
                for page in unverified:
                    show_page_card(page)
            to_learn = analysis.get("skills_to_learn") or []
            if to_learn:
                st.write("The 2 skills that would unlock the most matches for you: "
                         f"**{', '.join(to_learn[:2])}**")
        else:
            top_fit = max([m.get("fit_score") for m in live
                           if isinstance(m.get("fit_score"), int)] or [0])
            m1, m2, m3 = st.columns(3)
            m1.metric("Open right now", len(live))
            m2.metric("More boards", len(pages))
            m3.metric("Top fit", f"{top_fit}/100" if top_fit else "-")

            if stats.get("links_unverified"):
                st.caption("Link re-checks were blocked from this network, so "
                           "the postings below come from the sites' search "
                           "pages without a second verification.")
            if analysis:
                show_analysis(analysis)

            tab_live, tab_boards = st.tabs(
                [f"Open right now ({len(live)})",
                 f"More boards ({len(pages)})"])
            with tab_live:
                if live:
                    for i, match in enumerate(live):
                        show_match_card(i, match, analysis)
                else:
                    st.info("No postings we could read automatically just now - "
                            "the boards tab still has live searches.")
            with tab_boards:
                if pages:
                    for page in pages:
                        show_page_card(page)
                else:
                    st.info("The board search pages were unreachable just now.")

        st.divider()
        st.caption("Every link above was fetched or checked just now. If a posting "
                   "was filled between our check and your click, the site will say so.")

    st.divider()
    with st.expander("Privacy"):
        st.markdown(
            "- Your resume is processed in memory for this session only. "
            "Nothing is written to disk or a database.\n"
            "- Resume text is sent to the Gemini API to read your skills and "
            "draft your application message.\n"
            "- Internship listings are fetched live from public search pages. "
            "We never store or alter them.\n"
            "- No accounts, no tracking, no ads.")
    st.caption("Built for Code for a Billion 2026.")


if __name__ == "__main__":
    main()
