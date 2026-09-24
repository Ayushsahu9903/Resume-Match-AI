"""Scores one resume against one job description.

Reuses the same scoring rules as the original batch pipeline
(services/Rules.py) — degree matching, major matching, and AI-based
semantic skill matching — but works directly on plain lists for a single
resume/job pair instead of iterating over a pandas dataframe of many.
"""
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from Resources import DEGREES_IMPORTANCE


class ResumeJobMatcher:

    # Cached once per process — loading this ~420MB model on every request
    # is what made the original batch pipeline slow/crash-prone in
    # production, so it's shared across all matches the same way
    # services/Rules.py caches it.
    _model = None

    def __init__(self, labels):
        self.labels = labels
        self.degrees_importance = DEGREES_IMPORTANCE
        if ResumeJobMatcher._model is None:
            ResumeJobMatcher._model = SentenceTransformer('all-MiniLM-L6-v2')
        self.model = ResumeJobMatcher._model

    def get_major_category(self, major):
        for category, majors in self.labels['MAJOR'].items():
            if major in majors:
                return category
        return None

    def degree_score(self, resume_degrees, job_min_degree_level):
        """1.0 = resume meets/exceeds the job's minimum degree, 0.5 = close
        but under, 0 = no usable degree info on either side."""
        if not job_min_degree_level or job_min_degree_level not in self.degrees_importance:
            return 0.0
        job_min_degree = self.degrees_importance[job_min_degree_level]
        match_scores = [
            self.degrees_importance[d] - job_min_degree
            for d in resume_degrees if d in self.degrees_importance
        ]
        if not match_scores:
            return 0.0
        best = max(match_scores)
        if best >= 2:
            return 0.5
        elif best >= 0:
            return 1.0
        return 0.0

    def major_score(self, resume_majors, job_majors):
        """1.0 = an exact major match, 0.5 = same major category, 0 = no relation."""
        if not job_majors:
            return 0.0
        job_categories = [self.get_major_category(m) for m in job_majors]
        score = 0.0
        for r in resume_majors:
            if r in job_majors:
                return 1.0
            if self.get_major_category(r) in job_categories:
                score = 0.5
        return score

    def skills_score(self, job_skills, resume_skills):
        """Semantic similarity between required and resume skills using the
        sentence-transformer model — exact word matches count fully, and
        near-synonyms (e.g. 'ML' vs 'machine learning') still get partial
        credit if the embeddings are close enough."""
        if not job_skills or not resume_skills:
            return 0.0
        score = 0
        sen = job_skills + resume_skills
        sen_embeddings = self.model.encode(sen)
        for i in range(len(job_skills)):
            if job_skills[i] in resume_skills:
                score += 1
            else:
                sims = cosine_similarity([sen_embeddings[i]], sen_embeddings[len(job_skills):])[0]
                if len(sims) and max(sims) >= 0.4:
                    score += max(sims)
        return round(score / len(job_skills), 3)

    def match(self, resume_entities, job_entities):
        degree = self.degree_score(resume_entities.get('degrees', []), job_entities.get('minimum_degree_level'))
        major = self.major_score(resume_entities.get('majors', []), job_entities.get('majors', []))
        skills = self.skills_score(job_entities.get('skills', []), resume_entities.get('skills', []))
        overall = round((degree + major + skills) / 3, 3)
        return {
            "degree_match": round(degree, 3),
            "major_match": round(major, 3),
            "skills_match": round(skills, 3),
            "overall_score": overall,
            "overall_percentage": round(overall * 100, 1),
        }
