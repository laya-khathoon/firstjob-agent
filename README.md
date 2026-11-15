# FirstJob Agent

Find internships you actually qualify for. Built for Code for a Billion 2026 (Code for India), track: Tech Employment for Youth.

**Live demo:** https://firstjob-agent.streamlit.app/

## What it does
- Paste your resume (or upload a PDF) and answer 3 quick questions.
- Get real, currently open internships ranked by fit score (0-100), each with a direct apply link and one line on why you fit or what skill is missing.
- Pick one and get a tailored application message drafted from your own resume.
- No invented listings: every match links to a real posting or a live search page on the site itself, and every link is checked before it is shown.
- Nothing is stored: your resume stays in the session only.

## Run it locally
```
pip install -r requirements.txt
python -m streamlit run app.py
```

The app needs a free Google Gemini API key for resume analysis, fit scores and application drafts:
1. Get a key free at https://aistudio.google.com/apikey (no card needed).
2. Either set it as an environment variable: `GEMINI_API_KEY=your-key`
3. Or, on Streamlit Cloud: app Settings -> Secrets -> add `GEMINI_API_KEY = "your-key"`, then restart.

No key? The app still runs: resume analysis and fit scores fall back to a simple keyword scan, so you can try the whole flow before getting a key. Drafts and scores are better with Gemini.

## Sources it searches
- Live postings scraped from Internshala search pages (Internshala serves its listings in the page HTML).
- Live board and search pages for Unstop and the AICTE National Internship Portal, linked so the student can browse current openings there directly (Unstop blocks bots and the AICTE portal renders with JavaScript, so their individual postings cannot be fetched programmatically).

Every link returned is fetched and checked before it is shown; anything that cannot be verified is labeled as such.

## Honest limits
- Coverage is only as good as the public boards above - many internships are only on LinkedIn or company career pages, which do not allow scraping.
- The Gemini free tier has daily quota limits; when quota runs out the app falls back to keyword matching until it resets.

## License
MIT - see LICENSE.
