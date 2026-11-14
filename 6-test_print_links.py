"""Print every link FirstJob Agent would show, with a live HTTP check.

No API key needed: this uses the keyword-scan fallback for resume analysis.
Run:  python test_print_links.py
"""
from resume_parser import analyze_resume
from internship_searcher import search_internships, link_works


def main():
    with open("sample_resume.txt", encoding="utf-8") as f:
        resume_text = f.read()

    analysis = analyze_resume(resume_text, ["AI/ML", "web development", "data"],
                              "Both", False)
    keywords = analysis.get("search_keywords") or []
    print(f"Search keywords: {keywords}\n")

    results = search_internships(keywords)

    print("== Live postings ==")
    for m in results.get("live") or []:
        ok = link_works(m.get("url") or "")
        print(f"[{'OK' if ok else 'FAIL'}] {m.get('title')} | "
              f"{m.get('company') or 'no-company'} | {m.get('stipend') or 'stipend?'}")
        print(f"        {m.get('url')}")

    print("\n== Search pages ==")
    for p in results.get("pages") or []:
        print(f"[OK] {p.get('site')} - {p.get('keyword')}: {p.get('url')}")

    if not results.get("live") and not results.get("pages"):
        print("NOTHING FOUND - do not ship until this prints links.")


if __name__ == "__main__":
    main()
