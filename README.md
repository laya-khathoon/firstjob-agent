# FirstJob Agent

Find internships you actually qualify for. Built for Code for a Billion 2026 (Code for India), track: Other.

**Live demo (Vercel):** https://firstjob-agent.vercel.app/

**Previous Streamlit demo, kept as a backup:** https://firstjob-agent.streamlit.app/

The Vercel version has a static web interface, PDF/text resume analysis, live board searches and reviewable application drafts. Setup, limits and Windows sync steps: [Vercel deployment guide](VERCEL_DEPLOYMENT.md).

Vercel fit scores are keyword estimates. Work mode and stipend are preferences, not verified listing filters. AI features depend on the configured Gemini model and available free-tier quota; basic search still works when AI is unavailable.

## What it does
- Paste your resume (or upload a PDF) and answer 3 quick questions.
- Get real, currently open internships ranked by fit score (0-100), each with a direct apply link and one line on why you fit or what skill is missing.
- Pick one and get a tailored application message drafted from your own resume.
- No invented listings: every match links to a real posting or a live search page on the site itself, and every link is checked before it is shown.
- Nothing is stored: your resume stays in the session only.

## How it is organized
- `public/index.html` and `api/index.py` - the Vercel interface and stateless Python API.
- `app.py` - the original Streamlit app (resume upload, questions, results, drafts).
- `resume_parser.py` - resume analysis and fit scoring; uses Gemini when a key is set and a keyword scan when it is not.
- `internship_searcher.py` - live posting search and link checks (Internshala, Unstop, AICTE portal).
- `application_drafter.py` - the tailored application message for a chosen match.
- `test_*.py` - offline tests (`python -m pytest`); the fallback paths and link building are covered without network or API calls.

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

## Run the tests
```
python -m pytest
```
The test suite runs fully offline (no API key or network needed): resume parsing, fit scoring, internship-page parsing, Gemini JSON handling and apply-link printing.

## License
MIT - see LICENSE.

*Live demo:* https://firstjob-agent.streamlit.app/
