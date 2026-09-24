# Resume Match AI

**[🔗 Try it live →](https://resume-match-ai-p4q2.onrender.com/)**

Upload a resume (PDF/DOCX), paste a job description, and get back a match
score — with a breakdown of degree, major, and AI-based skill similarity.

> Free-tier hosting: the live demo may take 30-60s to wake up on the first
> request after a period of inactivity — that's normal, not a bug.

---

## Architecture

One FastAPI app, one Docker image, one deployment — no database, no
separate frontend build.

```
Browser
   │  GET  /              → frontend/index.html (the matcher UI)
   │  GET  /static/*      → frontend/static/ (CSS, JS)
   │  GET  /api/health    → API status
   │  POST /api/match     → score one resume against one job description
   ▼
FastAPI (main.py)
   │
   ├── services/ResumeFileParser.py    extract text from an uploaded PDF/DOCX
   ├── services/EntityExtraction.py    spaCy: pull degree/major/skills out of text
   └── services/ResumeJobMatcher.py    score rules + sentence-transformer model
```

The dashboard (`frontend/`) is plain HTML/CSS/JS — no build step, no
npm/node needed. It calls `POST /api/match` on the same origin.

### How the score is calculated

For a resume/job pair:

1. **Degree match** — does the resume's degree meet the job's minimum degree level? (1.0 = yes, 0.5 = close but under, 0 = no)
2. **Major match** — is the resume's major literally accepted by the job (1.0), in the same category as an accepted major (0.5), or unrelated (0)?
3. **Skills match** — each required skill is compared against the resume's skills using the `all-MiniLM-L6-v2` sentence-transformer model. Exact matches count fully; near-synonyms (e.g. "ML" vs "machine learning") get partial credit based on embedding similarity.

The overall score is the average of the three, shown as a percentage.

Degree/major/skill recognition is pattern-based (spaCy entity rules against
curated lists in `Resources/data/*.jsonl`), not free-form language
understanding — very unconventional phrasing on either side may not be
picked up.

---

## Running locally

### With Docker (recommended — matches production)

```bash
docker compose up --build
```

Starts the API + dashboard at http://localhost:8000.

### Without Docker

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://localhost:8000.

---

## Deploying

Live at **[resume-match-ai-p4q2.onrender.com](https://resume-match-ai-p4q2.onrender.com/)**,
running on [Render](https://render.com)'s free Docker web service tier via
`render.yaml`. To deploy your own copy: fork the repo, create a Web Service
on Render pointed at it, and deploy.

The Dockerfile installs a CPU-only PyTorch build and pre-downloads the
sentence-transformer model at build time, so the first request doesn't wait
on a model download.

---

## Tech stack

**Backend:** FastAPI, spaCy, sentence-transformers, scikit-learn, pypdf, python-docx
**Frontend:** static HTML/CSS/JS (no framework, no build step)
**Infra:** Docker, docker-compose, Render
