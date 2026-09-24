"""Runs the same spaCy entity-ruler patterns used for job descriptions
against arbitrary free text — either a job description or resume text —
to pull out degree level(s), majors, and skills.

This generalizes what services/JobInfoExtraction.py did for the old
dataframe-based sample pipeline, so the same pattern files
(Resources/data/*.jsonl) can be reused for a single resume/job pair
without needing a pandas dataframe in the loop.
"""
from spacy.lang.en import English
from Resources import DEGREES_IMPORTANCE


class EntityExtractor:

    def __init__(self, skills_patterns_path, majors_patterns_path, degrees_patterns_path):
        self.skills_patterns_path = skills_patterns_path
        self.majors_patterns_path = majors_patterns_path
        self.degrees_patterns_path = degrees_patterns_path

    @staticmethod
    def _run_ruler(patterns_path, text):
        nlp = English()
        ruler = nlp.add_pipe("entity_ruler")
        ruler.from_disk(patterns_path)
        doc = nlp(text)
        return doc.ents

    def extract_degrees(self, text):
        """Returns the list of degree levels mentioned (e.g. ['BS-LEVEL'])."""
        levels = []
        for ent in self._run_ruler(self.degrees_patterns_path, text):
            parts = ent.label_.split('|')
            if parts[0] == 'DEGREE' and parts[1] not in levels:
                levels.append(parts[1])
        return levels

    def extract_majors(self, text):
        """Returns the list of majors mentioned, e.g. ['computer science']."""
        majors = []
        for ent in self._run_ruler(self.majors_patterns_path, text):
            parts = ent.label_.split('|')
            if parts[0] == 'MAJOR':
                major = parts[2].replace('-', ' ')
                if major not in majors:
                    majors.append(major)
        return majors

    def extract_skills(self, text):
        """Returns the list of skills mentioned, e.g. ['python', 'sql']."""
        skills = []
        for ent in self._run_ruler(self.skills_patterns_path, text):
            parts = ent.label_.split('|')
            if parts[0] == 'SKILL':
                skill = parts[1].replace('-', ' ')
                if skill not in skills:
                    skills.append(skill)
        return skills

    def extract_all(self, text):
        return {
            "degrees": self.extract_degrees(text),
            "majors": self.extract_majors(text),
            "skills": self.extract_skills(text),
        }


def minimum_degree_level(levels):
    """Given a list of degree levels found in text, return the lowest one
    (i.e. the minimum bar), or None if no degree was mentioned at all."""
    valid = [d for d in levels if d in DEGREES_IMPORTANCE]
    if not valid:
        return None
    return min(valid, key=lambda d: DEGREES_IMPORTANCE[d])
