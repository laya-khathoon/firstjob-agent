# FirstJob Agent on Vercel

The Vercel version uses a static, mobile-friendly web page and a stateless Python function. It does not try to run Streamlit inside a serverless function.

## Files

- `public/index.html`: resume upload/paste, preferences, results and draft review.
- `api/index.py`: PDF extraction, bounded Gemini requests, internship search and draft generation.
- `vercel.json`: static output, function duration and security headers.
- The original `app.py`, shared Python modules and `.streamlit` settings remain in place for the existing Streamlit app.

## Deploy again

1. Import `laya-khathoon/firstjob-agent` in Vercel, using the free Hobby team.
2. Use production branch `main`, root directory `./` and Application Preset `Other`.
3. The repository configuration sets the output directory to `public`. Leave the build command empty.
4. In Vercel's private environment settings add `GEMINI_API_KEY` as a Secret for Production and Preview. Never commit a key or put it into the HTML. Also set the non-secret config variable `GEMINI_MODEL` to a model currently available to that key. This deployment was tested with `gemini-3.6-flash` on November 22, 2026; the older 2.5 model names returned 404 for this key.
5. Deploy, then open the production URL. Submit a fictional resume and confirm results render. Try a PDF, validation errors and application drafting.
6. Changing an environment variable requires another deployment before that value is used by the running app.

`GEMINI_MODEL` selects the model. Without it, the code tries older 2.5 names that may no longer be available to your key, so keep the verified model setting when redeploying. Requests have bounded timeouts. If Gemini is unavailable or quota is exhausted, the UI labels basic keyword analysis clearly. Drafting needs a working Gemini key and quota.

## What the results mean

- Postings come from public internship-board pages, never an AI-generated listing.
- Boards may block automated requests. If that happens, the app offers explicitly labelled search-page links instead of claiming it found verified vacancies.
- Fit scores in the Vercel interface are keyword estimates, not hiring predictions.
- Work mode and stipend are preferences, not guaranteed listing filters. Check actual eligibility, location, pay and availability on the source.
- Drafts are for review and editing. The app never sends applications.

## Privacy and runtime

The app does not save resumes to a database, filesystem or browser storage. Resume text is sent to Gemini when configured. Hosting and API providers may retain operational data under their own policies. Use fictional resumes for tests and remove private contact details if desired.

The static page avoids Streamlit's sleeping-app screen. Python cold starts, network requests and AI calls can still take time. Vercel and Gemini free-tier limits still apply. No paid services are required by this implementation.

PDFs must contain selectable text and be smaller than 2 MB. Pasted text takes priority when both inputs are provided. Results are hidden when inputs change.

## Sync the Windows git clone

```powershell
cd C:\Users\DELL\Documents\firstjob-agent-git
git status
git pull --ff-only origin main
```

If `git status` shows local work, keep it safe before pulling. The older AgentFoundry folder `firstjob-agent` is not the git clone. Pulling updates the code, not `.streamlit/secrets.toml` or any secret.

The Streamlit app still runs with `python -m streamlit run app.py`. To run the Vercel version locally, use Vercel CLI `vercel dev` from the repository root and configure a local environment variable separately.
