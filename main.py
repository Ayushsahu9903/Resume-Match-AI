import json
import logging

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from services.EntityExtraction import EntityExtractor, minimum_degree_level
from services.ResumeJobMatcher import ResumeJobMatcher
from services.ResumeFileParser import extract_text_from_upload, UnsupportedFileType, UnreadableFile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resume-match-ai")

app = FastAPI(
    title="Resume Match AI",
    description="Upload a resume, paste a job description, get a match score.",
    version="1.0.0",
)

# Permissive CORS so the API can be called from a separately-hosted frontend
# too, if you ever split it out. Tighten allow_origins to your real domain(s)
# if that matters for your deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Frontend ---
# The dashboard lives in ./frontend and is served alongside the API from the
# same FastAPI app/Docker image — no separate frontend deployment, no CORS
# to configure between them, one process to run.
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")


@app.get("/api/health")
async def health():
    return {
        "message": "✅ Resume Match AI API is running.",
        "docs": "/docs",
        "endpoints": ["/api/match"],
    }


# --- Entity extraction + matching, loaded once at startup ---
_DEGREES_PATTERNS = "Resources/data/degrees.jsonl"
_MAJORS_PATTERNS = "Resources/data/majors.jsonl"
_SKILLS_PATTERNS = "Resources/data/skills.jsonl"
_entity_extractor = EntityExtractor(_SKILLS_PATTERNS, _MAJORS_PATTERNS, _DEGREES_PATTERNS)

with open("Resources/data/labels.json") as _fp:
    _labels = json.load(_fp)
_matcher = ResumeJobMatcher(_labels)


@app.post("/api/match")
async def match_resume_to_job(
    job_description: str = Form(...),
    resume: UploadFile = File(...),
):
    if not job_description or not job_description.strip():
        raise HTTPException(status_code=400, detail="Job description can't be empty.")

    content = await resume.read()
    try:
        resume_text = extract_text_from_upload(resume.filename, content)
    except (UnsupportedFileType, UnreadableFile) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    job_text = job_description.replace(". ", " ")
    resume_text_normalized = resume_text.replace(". ", " ")

    job_degrees = _entity_extractor.extract_degrees(job_text)
    job_entities = {
        "minimum_degree_level": minimum_degree_level(job_degrees),
        "majors": _entity_extractor.extract_majors(job_text),
        "skills": _entity_extractor.extract_skills(job_text),
    }
    resume_entities = _entity_extractor.extract_all(resume_text_normalized)

    result = _matcher.match(resume_entities, job_entities)

    return {
        "filename": resume.filename,
        "job": job_entities,
        "resume": resume_entities,
        **result,
    }
