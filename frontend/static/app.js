const form = document.getElementById('matchForm');
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('resumeFile');
const dzIdle = document.getElementById('dzIdle');
const dzFile = document.getElementById('dzFile');
const dzFilename = document.getElementById('dzFilename');
const clearFileBtn = document.getElementById('clearFile');
const jobDescription = document.getElementById('jobDescription');
const submitBtn = document.getElementById('submitBtn');
const statusLine = document.getElementById('statusLine');
const errorBanner = document.getElementById('errorBanner');
const results = document.getElementById('results');

let selectedFile = null;

function setFile(file) {
  selectedFile = file || null;
  if (selectedFile) {
    dzIdle.style.display = 'none';
    dzFile.style.display = 'flex';
    dzFile.style.flexDirection = 'column';
    dzFile.style.alignItems = 'center';
    dzFile.style.gap = '8px';
    dzFilename.textContent = selectedFile.name;
    dropzone.classList.add('has-file');
  } else {
    dzIdle.style.display = 'flex';
    dzIdle.style.flexDirection = 'column';
    dzIdle.style.alignItems = 'center';
    dzIdle.style.gap = '8px';
    dzFile.style.display = 'none';
    dropzone.classList.remove('has-file');
    fileInput.value = '';
  }
}

fileInput.addEventListener('change', (e) => {
  const file = e.target.files[0];
  if (file) setFile(file);
});

clearFileBtn.addEventListener('click', (e) => {
  e.preventDefault();
  e.stopPropagation();
  setFile(null);
});

['dragenter', 'dragover'].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
  });
});
['dragleave', 'drop'].forEach((evt) => {
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
  });
});
dropzone.addEventListener('drop', (e) => {
  const file = e.dataTransfer.files[0];
  if (file) {
    fileInput.files = e.dataTransfer.files;
    setFile(file);
  }
});

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.add('visible');
}
function clearError() {
  errorBanner.textContent = '';
  errorBanner.classList.remove('visible');
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function renderChips(container, items, options = {}) {
  const { matchedAgainst = null, emptyText = 'none found' } = options;
  container.innerHTML = '';
  if (!items || items.length === 0) {
    const span = document.createElement('span');
    span.className = 'chip empty';
    span.textContent = emptyText;
    container.appendChild(span);
    return;
  }
  items.forEach((item) => {
    const span = document.createElement('span');
    span.className = 'chip';
    if (matchedAgainst && matchedAgainst.includes(item)) {
      span.classList.add('matched');
    }
    span.textContent = item;
    container.appendChild(span);
  });
}

function pct(fraction) {
  return `${Math.round((fraction || 0) * 100)}%`;
}

function renderResults(data) {
  document.getElementById('scoreNumber').textContent = `${data.overall_percentage}%`;

  document.getElementById('degreeVal').textContent = pct(data.degree_match);
  document.getElementById('degreeBar').style.width = pct(data.degree_match);
  document.getElementById('majorVal').textContent = pct(data.major_match);
  document.getElementById('majorBar').style.width = pct(data.major_match);
  document.getElementById('skillsVal').textContent = pct(data.skills_match);
  document.getElementById('skillsBar').style.width = pct(data.skills_match);

  const resume = data.resume || {};
  const job = data.job || {};

  renderChips(document.getElementById('resumeDegrees'), resume.degrees, { emptyText: 'none detected' });
  renderChips(document.getElementById('resumeMajors'), resume.majors, {
    matchedAgainst: job.majors || [], emptyText: 'none detected'
  });
  renderChips(document.getElementById('resumeSkills'), resume.skills, {
    matchedAgainst: job.skills || [], emptyText: 'none detected'
  });

  renderChips(document.getElementById('jobDegree'), job.minimum_degree_level ? [job.minimum_degree_level] : [], {
    emptyText: 'not specified'
  });
  renderChips(document.getElementById('jobMajors'), job.majors, {
    matchedAgainst: resume.majors || [], emptyText: 'not specified'
  });
  renderChips(document.getElementById('jobSkills'), job.skills, {
    matchedAgainst: resume.skills || [], emptyText: 'not specified'
  });

  results.classList.add('visible');
  results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  clearError();

  if (!selectedFile) {
    showError('Add a resume file (PDF or DOCX) first.');
    return;
  }
  if (!jobDescription.value.trim()) {
    showError('Paste a job description first.');
    return;
  }

  const formData = new FormData();
  formData.append('resume', selectedFile);
  formData.append('job_description', jobDescription.value);

  submitBtn.disabled = true;
  submitBtn.textContent = 'Analyzing…';
  statusLine.textContent = 'Reading the resume and scoring against the job description — this can take a bit on the first run.';
  results.classList.remove('visible');

  try {
    const res = await fetch('/api/match', { method: 'POST', body: formData });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || `Request failed (${res.status})`);
    }
    statusLine.textContent = '';
    renderResults(data);
  } catch (err) {
    statusLine.textContent = '';
    showError(err.message || 'Something went wrong while matching.');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Analyze match';
  }
});
