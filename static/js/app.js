let profile = { age: 18, group: 'adulte' };
let content = { videos: [], quiz: [], scams: [] };
let quizIndex = 0;
let quizScore = 0;

const labels = {
  enfant: 'enfant',
  adolescent: 'adolescent',
  adulte: 'adulte',
  senior: 'senior'
};

const ageMessages = {
  enfant: "Bienvenue ! Ici, tu découvres l’IA avec des mots simples, des exemples et des jeux.",
  adolescent: "Bienvenue ! Découvre comment utiliser l’IA pour apprendre, créer et vérifier les informations.",
  adulte: "Bienvenue ! Cette plateforme aide à comprendre l’IA, ses usages, ses limites et les bons réflexes.",
  senior: "Bienvenue. Les textes sont agrandis, les boutons sont simples, et vous pouvez écouter les contenus."
};

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  if (!response.ok) throw new Error('Erreur réseau');
  return response.json();
}

document.getElementById('ageForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const age = Number(document.getElementById('age').value);
  profile = await api('/api/profile', { method: 'POST', body: JSON.stringify({ age }) });
  document.body.className = profile.group;
  document.getElementById('ageGate').classList.add('d-none');
  document.getElementById('app').classList.remove('d-none');
  document.getElementById('profileMessage').textContent = ageMessages[profile.group];
  content = await api('/api/content');
  renderVideos();
  renderQuiz();
  renderScam();
  loadRanking();
});

function renderVideos() {
  const grid = document.getElementById('videoGrid');
  grid.innerHTML = content.videos.map((title, index) => `
    <div class="col-md-6 col-lg-3">
      <article class="official-card video-card p-4">
        <div class="video-icon mb-3" aria-hidden="true">▶</div>
        <h3 class="h5 fw-bold">${title}</h3>
        <p class="text-secondary">Vidéo pédagogique de 10 minutes avec exemples, résumé et quiz.</p>
        <button class="btn btn-outline-primary w-100" onclick="selectVideo('${title.replace(/'/g, "\\'")}')">Voir le parcours</button>
      </article>
    </div>
  `).join('');
}

function selectVideo(title) {
  speak(`Vous avez choisi le parcours ${title}. Après la vidéo, vous pourrez répondre au quiz.`);
  document.getElementById('quiz').scrollIntoView({ behavior: 'smooth' });
}

function renderQuiz() {
  const box = document.getElementById('quizBox');
  const q = content.quiz[quizIndex];
  if (!q) {
    const badge = quizScore >= 2 ? '🏅 Badge Vigilance IA' : '🎓 Badge Découverte IA';
    box.innerHTML = `
      <h3 class="fw-bold">Quiz terminé</h3>
      <p class="fs-4">Score : <strong>${quizScore}/${content.quiz.length}</strong></p>
      <span class="badge-award">${badge}</span>
      <div class="mt-3">
        <label class="form-label">Nom pour le classement</label>
        <input id="rankingName" class="form-control" value="Citoyen anonyme">
        <button class="btn btn-primary btn-lg mt-3" onclick="saveQuizScore()">Enregistrer mon score</button>
        <button class="btn btn-outline-primary btn-lg mt-3" onclick="restartQuiz()">Recommencer</button>
      </div>`;
    return;
  }
  box.innerHTML = `
    <p class="eyebrow">Question ${quizIndex + 1}/${content.quiz.length}</p>
    <h3 class="fw-bold">${q.question}</h3>
    <div class="mt-3">${q.choices.map((choice, i) => `<button class="answer-btn" onclick="answerQuiz(${i})">${choice}</button>`).join('')}</div>
  `;
}

function answerQuiz(choice) {
  const q = content.quiz[quizIndex];
  const buttons = document.querySelectorAll('.answer-btn');
  buttons.forEach((btn, i) => {
    btn.disabled = true;
    if (i === q.answer) btn.classList.add('correct');
    if (i === choice && i !== q.answer) btn.classList.add('wrong');
  });
  if (choice === q.answer) quizScore++;
  const result = document.getElementById('quizResult');
  result.classList.remove('d-none');
  result.textContent = q.explanation;
  setTimeout(() => {
    result.classList.add('d-none');
    quizIndex++;
    renderQuiz();
  }, 1400);
}

function restartQuiz() {
  quizIndex = 0;
  quizScore = 0;
  renderQuiz();
}

async function saveQuizScore() {
  const name = document.getElementById('rankingName').value;
  const data = await api('/api/quiz/submit', { method: 'POST', body: JSON.stringify({ name, score: quizScore, age_group: profile.group }) });
  renderRanking(data);
  document.getElementById('classements').scrollIntoView({ behavior: 'smooth' });
}

async function loadRanking() {
  const data = await api(`/api/ranking?age_group=${profile.group}`);
  renderRanking(data);
}

function renderRanking(data) {
  document.getElementById('nationalRanking').innerHTML = (data.national || []).map(s => `<li>${s.name} — ${s.score} pts</li>`).join('') || '<li>Aucun score pour le moment</li>';
  document.getElementById('ageRanking').innerHTML = (data.age_group || []).map(s => `<li>${s.name} — ${s.score} pts</li>`).join('') || '<li>Aucun score pour cette tranche d’âge</li>';
}

document.getElementById('sendPrompt').addEventListener('click', async () => {
  const prompt = document.getElementById('promptInput').value;
  const output = document.getElementById('promptOutput');
  output.innerHTML = '<p>Analyse en cours...</p>';
  try {
    const data = await api('/api/prompt', { method: 'POST', body: JSON.stringify({ prompt, age_group: profile.group }) });
    output.innerHTML = `
      <h3 class="h5 fw-bold">Réponse de l’IA</h3><p>${escapeHtml(data.answer)}</p>
      <h3 class="h5 fw-bold mt-4">Conseils pour améliorer</h3><ul>${data.tips.map(t => `<li>${t}</li>`).join('')}</ul>
      <h3 class="h5 fw-bold mt-4">Prompt amélioré</h3><div class="p-3 bg-light rounded">${escapeHtml(data.improved_prompt)}</div>
      <p class="small text-muted mt-3">Mode : ${data.used_openai ? 'API OpenAI activée' : 'réponse pédagogique locale'}</p>`;
    if (profile.group === 'senior') speak(data.answer);
  } catch (error) {
    output.innerHTML = '<p class="text-danger">Impossible d’analyser ce prompt pour le moment.</p>';
  }
});

function renderScam() {
  const scam = content.scams[Math.floor(Math.random() * content.scams.length)];
  document.getElementById('scamBox').innerHTML = `
    <p class="eyebrow">${scam.type}</p>
    <div class="scam-message mb-3">${scam.message}</div>
    <p class="fw-semibold">Cliquez sur les éléments suspects :</p>
    <div>${scam.suspects.map(s => `<button class="suspect-chip" onclick="this.classList.toggle('selected')">${s}</button>`).join('')}</div>
    <button class="btn btn-primary btn-lg mt-3" onclick="showScamAdvice('${escapeAttribute(scam.advice)}')">Voir l’explication</button>
    <button class="btn btn-outline-primary btn-lg mt-3" onclick="renderScam()">Nouvel exemple</button>
    <div id="scamAdvice" class="alert alert-warning d-none mt-3"></div>`;
}

function showScamAdvice(advice) {
  const box = document.getElementById('scamAdvice');
  box.textContent = advice;
  box.classList.remove('d-none');
  if (profile.group === 'senior') speak(advice);
}

document.getElementById('listenIntro').addEventListener('click', () => speak(ageMessages[profile.group]));
document.getElementById('micButton').addEventListener('click', () => {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) { alert('La reconnaissance vocale n’est pas disponible sur ce navigateur.'); return; }
  const rec = new Recognition();
  rec.lang = 'fr-FR';
  rec.onresult = (event) => {
    document.getElementById('promptInput').value = event.results[0][0].transcript;
    document.getElementById('prompts').scrollIntoView({ behavior: 'smooth' });
  };
  rec.start();
});

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'fr-FR';
  utterance.rate = profile.group === 'senior' ? 0.82 : 1;
  speechSynthesis.cancel();
  speechSynthesis.speak(utterance);
}

function escapeHtml(str) {
  return String(str).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}
function escapeAttribute(str) { return String(str).replace(/'/g, '&#39;').replace(/"/g, '&quot;'); }
