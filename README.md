# FirstJob Agent

Find internships you actually qualify for. Built for Code for a Billion 2026 (Code for India), track: Tech Employment for Youth.

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
3. Or, on Streamlit Cloud: app Settings -> Secrets -> add `GEMINI_API_KEY = "your-key"`.

Never paste the key into code or the README.

## Check every link the app shows
```
python test_print_links.py
```

## Built with
AgentFoundry (the official IDE of Code for a Billion) with SMART-Code, Python, Streamlit and the Google Gemini API (free tier).

## Sources it searches
AICTE Internship Portal, Internshala, Unstop, LinkedIn and Indeed.

## License
MIT - see LICENSE.
