const state = {
  user: null,
  progress: {
    score: 0,
    completed_videos: [],
    opened_videos: [],
    video_quiz_scores: {},
    prompt_usage: { used: 0, limit: 3, remaining: 3 },
    certificate_unlocked: false,
    threshold: 70,
  },
  content: null,
  currentVideo: null,
  currentScam: null,
  currentImage: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;',
  }[character]));
}

function getCsrfToken() {
  return $('meta[name="csrf-token"]')?.content || '';
}

function setCsrfToken(token) {
  const meta = $('meta[name="csrf-token"]');
  if (meta && token) meta.content = token;
}

async function api(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const headers = { ...(options.headers || {}) };
  if (options.body !== undefined && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) headers['X-CSRF-Token'] = getCsrfToken();

  const response = await fetch(path, {
    credentials: 'same-origin',
    ...options,
    method,
    headers,
  });
  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json') ? await response.json().catch(() => ({})) : {};
  if (data.csrf_token) setCsrfToken(data.csrf_token);
  if (!response.ok) {
    const message = data.errors?.join(' ') || data.message || data.error || 'Une erreur est survenue.';
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

function setMessage(element, text, type = 'success') {
  if (!element) return;
  element.textContent = text;
  element.className = `message ${type}`;
}

function clearMessage(element) {
  if (!element) return;
  element.textContent = '';
  element.className = 'message';
}

function labelRole(role) {
  return ({
    jeune: 'Jeune', enseignant: 'Enseignant', etablissement: 'Établissement scolaire', citoyen: 'Citoyen',
  })[role] || 'Citoyen';
}

function updateAuthUi() {
  const loggedIn = Boolean(state.user);
  $('#logoutBtn')?.classList.toggle('hidden', !loggedIn);
  $('#authNavLink').textContent = loggedIn ? 'Formation' : 'Connexion';
  $('#authNavLink').setAttribute('href', loggedIn ? '#espace' : '#connexion');
  $('#heroAccountBtn')?.classList.toggle('hidden', loggedIn);
  $('#courseAccessBtn')?.setAttribute('href', loggedIn ? '#espace' : '#connexion');
  $('#espace')?.classList.toggle('hidden', !loggedIn);
  $('#connexion')?.classList.toggle('hidden', loggedIn);

  const ageClasses = ['age-jeune', 'age-adulte', 'age-mature', 'age-senior', 'age-grand-senior'];
  document.body.classList.remove(...ageClasses);
  if (state.user) {
    const ageClass = state.user.age_group === 'grand_senior'
      ? 'age-grand-senior'
      : `age-${state.user.age_group}`;
    document.body.classList.add(ageClass);
    $('#welcomeTitle').textContent = `Bienvenue ${state.user.name}`;
    $('#welcomeText').textContent = `Profil : ${labelRole(state.user.role)} - votre progression est enregistrée dans cet espace.`;
  }
}

function updateProgress(progress) {
  state.progress = { ...state.progress, ...(progress || {}) };
  const score = Number(state.progress.score || 0);
  $('#scoreValue').textContent = score;
  $('#scoreRing')?.style.setProperty('--progress', `${score}%`);

  const unlocked = Boolean(state.progress.certificate_unlocked || state.progress.eligible);
  $('#certificateBtn')?.classList.toggle('hidden', !unlocked);
  $('#certStatus').textContent = unlocked ? 'Certification débloquée' : 'Certification verrouillée';
  $('#certHint').textContent = unlocked
    ? 'Bravo ! Votre certificat PDF est disponible.'
    : `Il reste ${Math.max(0, Number(state.progress.threshold || 70) - score)} point(s) à obtenir.`;

  renderPromptLimit();
  if (state.content) renderVideos();
}

async function loadSession() {
  const data = await api('/api/me');
  if (data.authenticated) {
    state.user = data.user;
    updateProgress(data.progress);
    updateAuthUi();
    await loadContent();
  } else {
    updateAuthUi();
  }
}

async function loadContent() {
  const data = await api('/api/content');
  state.content = data;
  updateProgress(data.progress);
  renderVideos();
  renderPromptExamples();
  renderAiStatus();
  renderScam();
  renderImageLab();
}

function renderVideos() {
  const grid = $('#videoGrid');
  if (!grid || !state.content) return;
  const completed = new Set(state.progress.completed_videos || []);
  const opened = new Set(state.progress.opened_videos || []);
  const quizScores = state.progress.video_quiz_scores || {};

  grid.innerHTML = state.content.videos.map((video) => {
    const done = completed.has(video.id);
    const wasOpened = opened.has(video.id);
    const quiz = quizScores[video.id];
    const comingSoon = !video.available;
    const localMissing = video.source_type === 'local' && video.media_ready === false;
    const status = comingSoon
      ? '<span class="status-badge neutral">Bientôt disponible</span>'
      : done
        ? '<span class="status-badge success">Vidéo terminée</span>'
        : wasOpened
          ? '<span class="status-badge info">Vidéo ouverte</span>'
          : '<span class="status-badge neutral">À commencer</span>';
    const quizStatus = quiz
      ? `<p class="module-score">QCM : <strong>${quiz.points}/${quiz.max_points}</strong></p>`
      : video.quiz.length
        ? '<p class="module-score">QCM : non réalisé</p>'
        : '';
    const warning = localMissing
      ? '<p class="inline-warning">Le fichier vidéo local sera disponible dès qu’il sera placé à la racine du projet.</p>'
      : '';
    const duration = video.duration
      ? `<span class="duration">${escapeHtml(video.duration)}</span>`
      : '';
    return `
      <article class="card video-card ${done ? 'done' : ''} ${comingSoon ? 'coming-soon' : ''}">
        <div class="card-topline">${duration}${status}</div>
        <h3>${escapeHtml(video.title)}</h3>
        <p>${escapeHtml(video.summary)}</p>
        <ul class="takeaways">${video.takeaways.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
        ${quizStatus}${warning}
        <button class="btn ${comingSoon ? 'btn-disabled' : 'btn-primary'} open-video" data-video-id="${escapeHtml(video.id)}" type="button" ${comingSoon ? 'disabled' : ''}>
          ${comingSoon ? 'Arrive bientôt' : 'Ouvrir la vidéo et le QCM'}
        </button>
      </article>`;
  }).join('');

  $$('.open-video:not([disabled])').forEach((button) => {
    button.addEventListener('click', () => openVideo(button.dataset.videoId));
  });
}

async function openVideo(videoId) {
  const result = await api(`/api/videos/${encodeURIComponent(videoId)}/open`, { method: 'POST', body: '{}' });
  state.currentVideo = result.video;
  updateProgress(result.progress);
  renderVideoDialog(result.video);
  $('#videoDialog').showModal();
}

function renderVideoDialog(video) {
  $('#videoDialogTitle').textContent = video.title;
  const player = $('#videoPlayer');
  if (video.source_type === 'embed') {
    player.innerHTML = `<div class="responsive-frame"><iframe src="${escapeHtml(video.source_url)}" title="${escapeHtml(video.title)}" allow="encrypted-media; fullscreen; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>`;
  } else if (video.source_type === 'local') {
	  player.innerHTML = `<video controls preload="metadata" playsinline><source src="${escapeHtml(video.source_url)}" type="video/mp4">Votre navigateur ne prend pas en charge la lecture vidéo.</video>`;
  } else {
    player.innerHTML = '<div class="coming-soon-panel">Cette vidéo arrive bientôt.</div>';
  }

  const quizForm = $('#videoQuizForm');
  quizForm.innerHTML = video.quiz.map((question, questionIndex) => `
    <fieldset class="question-card" data-question-index="${questionIndex}">
      <legend><strong>Question ${questionIndex + 1}</strong> - ${escapeHtml(question.question)}</legend>
      <div class="answers">
        ${question.choices.map((choice, choiceIndex) => `
          <label class="answer-line">
            <input type="radio" name="video-q${questionIndex}" value="${choiceIndex}">
            <span><strong>${String.fromCharCode(65 + choiceIndex)}.</strong> ${escapeHtml(choice)}</span>
          </label>`).join('')}
      </div>
      <div class="question-actions">
        <button class="btn btn-outline btn-small validate-question" data-question-index="${questionIndex}" type="button">Valider cette question</button>
        <span class="question-feedback" role="status" aria-live="polite"></span>
      </div>
    </fieldset>`).join('');
  $$('.validate-question').forEach((button) => {
    button.addEventListener('click', () => validateVideoQuestion(Number(button.dataset.questionIndex)));
  });
  $$('input[name^="video-q"]').forEach((input) => {
    input.addEventListener('change', () => {
      const card = input.closest('.question-card');
      card?.classList.remove('question-correct', 'question-incorrect', 'question-unanswered');
      const feedback = card?.querySelector('.question-feedback');
      if (feedback) feedback.textContent = '';
    });
  });
  clearMessage($('#videoQuizResult'));
}

function setQuestionFeedback(index, status, message) {
  const card = $(`.question-card[data-question-index="${index}"]`);
  if (!card) return;
  card.classList.remove('question-correct', 'question-incorrect', 'question-unanswered');
  if (status) card.classList.add(`question-${status}`);
  const feedback = card.querySelector('.question-feedback');
  if (feedback) feedback.textContent = message;
}

async function validateVideoQuestion(index) {
  if (!state.currentVideo) return;
  const selected = $(`input[name="video-q${index}"]:checked`);
  if (!selected) {
    setQuestionFeedback(index, 'unanswered', 'Sélectionnez une réponse avant de valider.');
    return;
  }
  const button = $(`.validate-question[data-question-index="${index}"]`);
  if (button) button.disabled = true;
  try {
    const data = await api(`/api/videos/${encodeURIComponent(state.currentVideo.id)}/quiz/check`, {
      method: 'POST',
      body: JSON.stringify({ question_index: index, answer: Number(selected.value) }),
    });
    setQuestionFeedback(index, data.correct ? 'correct' : 'incorrect', data.message);
  } catch (error) {
    setQuestionFeedback(index, null, error.message);
  } finally {
    if (button) button.disabled = false;
  }
}

async function completeCurrentVideo() {
  if (!state.currentVideo) return;
  const data = await api(`/api/videos/${encodeURIComponent(state.currentVideo.id)}/complete`, { method: 'POST', body: '{}' });
  updateProgress(data.progress);
  setMessage($('#videoQuizResult'), 'Vidéo marquée comme terminée. Vous pouvez maintenant valider le QCM.', 'success');
}

async function submitCurrentVideoQuiz() {
  if (!state.currentVideo) return;
  const answers = state.currentVideo.quiz.map((_, index) => {
    const selected = $(`input[name="video-q${index}"]:checked`);
    return selected ? Number(selected.value) : null;
  });
  const unanswered = answers
    .map((answer, index) => (answer === null ? index : null))
    .filter((index) => index !== null);
  if (unanswered.length) {
    unanswered.forEach((index) => setQuestionFeedback(index, 'unanswered', 'Cette question attend une réponse.'));
    const result = $('#videoQuizResult');
    result.className = 'message result-box warning';
    result.textContent = "Toutes les questions n'ont pas reçu de réponse. Répondez aux questions en jaune avant de valider le QCM.";
    $(`.question-card[data-question-index="${unanswered[0]}"]`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }
  const data = await api(`/api/videos/${encodeURIComponent(state.currentVideo.id)}/quiz`, {
    method: 'POST',
    body: JSON.stringify({ answers }),
  });
  updateProgress(data.progress);
  data.corrections.forEach((item, index) => {
    setQuestionFeedback(index, item.correct ? 'correct' : 'incorrect', item.correct ? 'Bonne réponse !' : 'Réponse incorrecte.');
  });
  const result = $('#videoQuizResult');
  result.className = 'message result-box';
  result.innerHTML = `
    <h3>Résultat : ${data.correct_count}/${data.question_count} bonnes réponses - ${data.points}/${data.max_points} points</h3>
    ${data.corrections.map((item, index) => `
      <div class="correction ${item.correct ? 'ok' : 'ko'}">
        <strong>${item.correct ? '✓' : '✕'} Question ${index + 1}</strong>
        ${item.correct ? '' : `<br>Bonne réponse : ${String.fromCharCode(65 + item.answer)}. ${escapeHtml(item.correct_text)}`}
      </div>`).join('')}`;
}

function renderPromptExamples() {
  const box = $('#promptExamples');
  if (!box || !state.content) return;
  box.innerHTML = state.content.prompt_examples.map((example) => `
    <article class="example">
      <span class="status-badge ${example.level === 'Excellent' ? 'success' : example.level === 'Moyen' ? 'info' : 'neutral'}">${escapeHtml(example.level)}</span>
      <p class="prompt-example-text">${escapeHtml(example.prompt)}</p>
      <p class="muted">${escapeHtml(example.explanation)}</p>
      <button class="btn btn-outline btn-small use-example" type="button" data-prompt="${escapeHtml(example.prompt)}">Utiliser cet exemple</button>
    </article>`).join('');
  $$('.use-example').forEach((button) => {
    button.addEventListener('click', () => {
      $('#promptInput').value = button.dataset.prompt;
      $('#promptInput').focus();
    });
  });
}

function renderAiStatus() {
  const notice = $('#aiConfigNotice');
  if (!notice || !state.content) return;
  if (state.content.ai.configured) {
    setMessage(notice, `Gemini est configuré avec le modèle ${state.content.ai.model}.`, 'success');
  } else {
    setMessage(notice, 'Gemini n’est pas encore configuré. Ajoutez GEMINI_API_KEY dans le fichier .env puis relancez le serveur.', 'error');
  }
}

function renderPromptLimit() {
  const box = $('#promptLimit');
  const usage = state.progress.prompt_usage || { used: 0, limit: 3, remaining: 3 };
  if (box) box.innerHTML = `<strong>${usage.remaining}</strong> essai(s) restant(s) sur ${usage.limit}.`;
  const button = $('#analyzePrompt');
  if (button) {
    button.disabled = usage.remaining <= 0;
    button.textContent = usage.remaining <= 0 ? 'Limite atteinte' : 'Tester mon prompt';
  }
}

function renderStringList(title, items) {
  if (!Array.isArray(items) || items.length === 0) return '';
  return `<h3>${escapeHtml(title)}</h3><ul class="advice-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>`;
}

async function analyzePrompt() {
  const prompt = $('#promptInput').value.trim();
  const output = $('#promptOutput');
  if (!prompt) {
    output.innerHTML = '<p class="message error">Écrivez d’abord un prompt à tester.</p>';
    return;
  }
  const button = $('#analyzePrompt');
  button.disabled = true;
  output.innerHTML = '<div class="loading"><span class="spinner" aria-hidden="true"></span><p>Le service IA analyse votre prompt. Plusieurs tentatives automatiques peuvent être nécessaires…</p></div>';
  try {
    const data = await api('/api/prompt/analyze', { method: 'POST', body: JSON.stringify({ prompt }) });
    updateProgress(data.progress);
    output.innerHTML = `
      <div class="output-heading"><h3>Score du prompt : ${data.points}/${data.max_points}</h3><span class="status-badge info">${escapeHtml(data.model)}</span></div>
      <div>${data.checks.map((check) => `
        <div class="criterion">
          <span>${escapeHtml(check.label)}<br><small class="muted">${escapeHtml(check.tip)}</small></span>
          <span class="pill ${check.ok ? 'ok' : 'ko'}">${check.ok ? 'OK' : 'À améliorer'}</span>
        </div>`).join('')}</div>
      ${renderStringList('Défauts repérés', data.defects)}
      <h3>Réponse au prompt initial</h3>
      <div class="prompt-box">${escapeHtml(data.answer)}</div>
      <h3>Prompt amélioré</h3>
      <div class="prompt-box emphasized">${escapeHtml(data.improved_prompt)}</div>
      ${renderStringList('Pourquoi cette version est meilleure', data.improvement_reasons)}
      <h3>Réponse au prompt amélioré</h3>
      <div class="prompt-box">${escapeHtml(data.improved_answer)}</div>
      ${renderStringList('Conseils pédagogiques', data.pedagogical_advice)}
      <p class="muted">Le prompt n'est pas stocké en clair par MEPA. Seule une empreinte technique est enregistrée.</p>`;
  } catch (error) {
    if (error.data?.prompt_usage) {
      state.progress.prompt_usage = error.data.prompt_usage;
      renderPromptLimit();
    }
    output.innerHTML = `<p class="message error">${escapeHtml(error.message)}</p>`;
  } finally {
    renderPromptLimit();
  }
}

function renderScam() {
  const box = $('#scamBox');
  if (!box || !state.content) return;
  const scenarios = state.content.scams;
  state.currentScam = scenarios[Math.floor(Math.random() * scenarios.length)];
  box.innerHTML = `
    <p class="eyebrow">${escapeHtml(state.currentScam.kind)}</p>
    <div class="scam-message">${escapeHtml(state.currentScam.message)}</div>
    <p><strong>Cliquez sur tous les signaux suspects.</strong></p>
    <div class="chip-grid" id="scamChips">
      ${state.currentScam.signs.map((sign) => `<button class="chip" data-key="${escapeHtml(sign.key)}" type="button">${escapeHtml(sign.label)}</button>`).join('')}
    </div>
    <div class="button-row"><button class="btn btn-primary" id="submitScam" type="button">Valider l'analyse</button><button class="btn btn-outline" id="newScam" type="button">Nouvel exemple</button></div>`;
  wireChips('#scamChips .chip');
  $('#newScam').addEventListener('click', renderScam);
  $('#submitScam').addEventListener('click', submitScam);
}

function renderImageLab() {
  const box = $('#imageLab');
  if (!box || !state.content) return;
  const exercises = state.content.image_exercises;
  state.currentImage = exercises[Math.floor(Math.random() * exercises.length)];
  box.innerHTML = `
    <div class="image-exercise">
      <p class="eyebrow">${escapeHtml(state.currentImage.title)}</p>
      <img src="${escapeHtml(state.currentImage.image)}" alt="${escapeHtml(state.currentImage.title)}">
      <p class="image-caption">${escapeHtml(state.currentImage.prompt_hint)}</p>
      <p><strong>Quels signes peuvent montrer que l'image est générée ou manipulée ?</strong></p>
      <div class="chip-grid" id="imageChips">
        ${state.currentImage.signs.map((sign) => `<button class="chip" data-key="${escapeHtml(sign.key)}" type="button">${escapeHtml(sign.label)}</button>`).join('')}
      </div>
      <div class="button-row"><button class="btn btn-primary" id="submitImage" type="button">Valider l'image</button><button class="btn btn-outline" id="newImage" type="button">Nouvelle image</button></div>
    </div>`;
  wireChips('#imageChips .chip');
  $('#newImage').addEventListener('click', renderImageLab);
  $('#submitImage').addEventListener('click', submitImageLab);
}

function wireChips(selector) {
  $$(selector).forEach((chip) => chip.addEventListener('click', () => {
    const selected = chip.classList.toggle('selected');
    chip.setAttribute('aria-pressed', String(selected));
  }));
}

function selectedKeys(selector) {
  return $$(selector).filter((chip) => chip.classList.contains('selected')).map((chip) => chip.dataset.key);
}

async function submitScam() {
  if (!state.currentScam) return;
  const data = await api('/api/scam/submit', {
    method: 'POST',
    body: JSON.stringify({ scenario_id: state.currentScam.id, selected: selectedKeys('#scamChips .chip') }),
  });
  updateProgress(data.progress);
  $('#scamResult').className = 'message result-box';
  $('#scamResult').innerHTML = `<h3>Message suspect : ${data.points}/${data.max_points} points</h3><p>${escapeHtml(data.details.explanation)}</p><p><strong>Trouvés :</strong> ${escapeHtml(data.details.found.join(', ') || 'aucun')}</p><p><strong>À repérer aussi :</strong> ${escapeHtml(data.details.missed.join(', ') || 'rien, bravo')}</p>`;
}

async function submitImageLab() {
  if (!state.currentImage) return;
  const data = await api('/api/image/submit', {
    method: 'POST',
    body: JSON.stringify({ exercise_id: state.currentImage.id, selected: selectedKeys('#imageChips .chip') }),
  });
  updateProgress(data.progress);
  $('#scamResult').className = 'message result-box';
  $('#scamResult').innerHTML = `<h3>Image synthétique : ${data.points}/${data.max_points} points</h3><p>${escapeHtml(data.details.explanation)}</p><p><strong>Signes trouvés :</strong> ${escapeHtml(data.details.found.join(', ') || 'aucun')}</p><p><strong>Signes manqués :</strong> ${escapeHtml(data.details.missed.join(', ') || 'rien, bravo')}</p>`;
}

function switchAuth(mode) {
  const register = mode === 'register';
  $('#registerForm').classList.toggle('hidden', !register);
  $('#loginForm').classList.toggle('hidden', register);
  $('#registerTab').classList.toggle('active', register);
  $('#loginTab').classList.toggle('active', !register);
  $('#registerTab').setAttribute('aria-selected', String(register));
  $('#loginTab').setAttribute('aria-selected', String(!register));
  clearMessage($('#authMessage'));
}

async function handleRegister(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  payload.consent = form.elements.consent.checked;
  try {
    const data = await api('/api/register', { method: 'POST', body: JSON.stringify(payload) });
    state.user = data.user;
    updateProgress(data.progress);
    updateAuthUi();
    await loadContent();
    location.hash = '#espace';
  } catch (error) {
    setMessage($('#authMessage'), error.message, 'error');
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.currentTarget).entries());
  try {
    const data = await api('/api/login', { method: 'POST', body: JSON.stringify(payload) });
    state.user = data.user;
    updateProgress(data.progress);
    updateAuthUi();
    await loadContent();
    location.hash = '#espace';
  } catch (error) {
    setMessage($('#authMessage'), error.message, 'error');
  }
}

async function logout() {
  await api('/api/logout', { method: 'POST', body: '{}' });
  state.user = null;
  state.content = null;
  state.progress = { score: 0, completed_videos: [], opened_videos: [], video_quiz_scores: {}, prompt_usage: { used: 0, limit: 3, remaining: 3 }, certificate_unlocked: false, threshold: 70 };
  updateAuthUi();
  location.hash = '#accueil';
}

async function deleteAccount() {
  const confirmed = confirm('Confirmer la suppression définitive du compte et de toutes les activités ?');
  if (!confirmed) return;
  const data = await api('/api/account/delete', { method: 'POST', body: '{}' });
  if (data.csrf_token) setCsrfToken(data.csrf_token);
  state.user = null;
  state.content = null;
  updateAuthUi();
  alert('Compte supprimé.');
  location.hash = '#accueil';
}

async function downloadCertificate() {
  const response = await fetch('/certificate/download', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'X-CSRF-Token': getCsrfToken() },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.message || data.error || 'Le certificat ne peut pas être téléchargé.');
  }
  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename=([^;]+)/i);
  const filename = match ? match[1].replace(/["']/g, '') : 'certificat-mepa.pdf';
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function wireTabs() {
  $$('.module-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      $$('.module-tab').forEach((item) => item.classList.remove('active'));
      $$('.module-panel').forEach((panel) => panel.classList.remove('active'));
      tab.classList.add('active');
      $(`#${tab.dataset.panel}`).classList.add('active');
    });
  });
}

function wireNav() {
  $('#navToggle')?.addEventListener('click', () => {
    const links = $('#navLinks');
    const open = !links.classList.contains('open');
    links.classList.toggle('open', open);
    $('#navToggle').setAttribute('aria-expanded', String(open));
  });
  $$('#navLinks a').forEach((link) => link.addEventListener('click', () => $('#navLinks').classList.remove('open')));
}

function init() {
  wireNav();
  wireTabs();
  $('#registerTab')?.addEventListener('click', () => switchAuth('register'));
  $('#loginTab')?.addEventListener('click', () => switchAuth('login'));
  $('#registerForm')?.addEventListener('submit', handleRegister);
  $('#loginForm')?.addEventListener('submit', handleLogin);
  $('#logoutBtn')?.addEventListener('click', () => logout().catch((error) => alert(error.message)));
  $('#analyzePrompt')?.addEventListener('click', analyzePrompt);
  $('#deleteAccountBtn')?.addEventListener('click', () => deleteAccount().catch((error) => alert(error.message)));
  $('#certificateBtn')?.addEventListener('click', () => downloadCertificate().catch((error) => alert(error.message)));
  $('#completeVideoBtn')?.addEventListener('click', () => completeCurrentVideo().catch((error) => setMessage($('#videoQuizResult'), error.message, 'error')));
  $('#submitVideoQuiz')?.addEventListener('click', () => submitCurrentVideoQuiz().catch((error) => setMessage($('#videoQuizResult'), error.message, 'error')));
  $('#closeVideoDialog')?.addEventListener('click', () => $('#videoDialog').close());
  $('#videoDialog')?.addEventListener('close', () => { $('#videoPlayer').innerHTML = ''; });
  $('#videoDialog')?.addEventListener('click', (event) => {
    if (event.target === $('#videoDialog')) $('#videoDialog').close();
  });
  loadSession().catch(() => updateAuthUi());
}

document.addEventListener('DOMContentLoaded', init);
