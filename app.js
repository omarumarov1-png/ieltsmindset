(() => {
  "use strict";

  // ======================================================================
  // Constants
  // ======================================================================
  const READING_TEST_SECONDS = 60 * 60;
  const LISTENING_SECTION_GAP_SECONDS = 3;

  const UI = {
    dashboardTitle: "Добро пожаловать в IELTSmindset",
    dashboardSub: "Готовьтесь к IELTS в формате, максимально приближённом к настоящему компьютерному экзамену.",
    overallBand: "Средний балл",
    noHistoryYet: "Пока нет пройденных тестов — начните с раздела «Чтение» или «Аудирование».",
    recentTests: "Недавние попытки",
    skillReading: "Чтение",
    skillReadingDesc: "3 текста, 40 вопросов, 60 минут. True/False/Not Given, Matching Headings, заполнение пропусков и другие типы заданий.",
    skillListening: "Аудирование",
    skillListeningDesc: "4 записи, 40 вопросов. Диалоги и монологи с носителями языка — британский, американский и австралийский акценты.",
    skillWriting: "Письмо",
    skillWritingDesc: "Задание 1 и Задание 2 с ИИ-проверкой по критериям IELTS. Скоро.",
    skillSpeaking: "Говорение",
    skillSpeakingDesc: "Части 1, 2 и 3 с записью ответа и обратной связью. Скоро.",
    comingSoon: "Скоро",
    startPractice: "Практика",
    startTest: "Полный тест",
    practiceMode: "Режим практики",
    practiceModeDesc: "Без ограничения времени. Можно повторно слушать аудио и проверять ответы сразу.",
    testMode: "Экзаменационный режим",
    testModeDesc: "Строго по времени, как на настоящем экзамене. Результат — только в конце.",
    backToHub: "Назад к списку",
    passage: "Текст",
    section: "Часть",
    testShort: "Тест",
    moduleAcademic: "Academic",
    moduleGeneral: "General Training",
    questions: "Вопросы",
    exitTest: "Выйти",
    flagQuestion: "Отметить",
    unflagQuestion: "Убрать отметку",
    reviewAnswers: "Проверить ответы",
    submitTest: "Завершить тест",
    submitConfirmTitle: "Завершить тест?",
    submitConfirmBody: "Вы ответили не на все вопросы. После завершения изменить ответы будет нельзя.",
    submitConfirmBodyAll: "Все вопросы отвечены. Проверьте свои ответы перед завершением.",
    cancel: "Отмена",
    confirmSubmit: "Завершить",
    yourBand: "Ваш балл",
    correctAnswers: "Правильных ответов",
    timeTaken: "Затрачено времени",
    reviewTitle: "Разбор ответов",
    yourAnswer: "Ваш ответ",
    correctAnswer: "Правильный ответ",
    backToDashboard: "На главную",
    tryAgain: "Пройти ещё раз",
    play: "Слушать",
    pause: "Пауза",
    nextSection: "Следующая часть",
    audioEnded: "Запись окончена",
    wordLimitWarn: (n) => `Не более ${n} ${wordForm(n)}`,
    trueFalseOptions: ["TRUE", "FALSE", "NOT GIVEN"],
    trueFalseLabelsRu: { TRUE: "ВЕРНО", FALSE: "НЕВЕРНО", "NOT GIVEN": "НЕТ ИНФОРМАЦИИ" },
    yesNoOptions: ["YES", "NO", "NOT GIVEN"],
    yesNoLabelsRu: { YES: "ДА", NO: "НЕТ", "NOT GIVEN": "НЕТ ИНФОРМАЦИИ" },
  };

  function wordForm(n) {
    return n === 1 ? "слова" : "слов";
  }

  // Russian numeral agreement: pick the form for n (e.g. ruPlural(21,"вопрос","вопроса","вопросов")).
  function ruPlural(n, one, few, many) {
    const mod10 = n % 10, mod100 = n % 100;
    if (mod10 === 1 && mod100 !== 11) return one;
    if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
    return many;
  }
  function questionsWord(n) { return ruPlural(n, "вопрос", "вопроса", "вопросов"); }
  function passagesWord(n) { return ruPlural(n, "текст", "текста", "текстов"); }
  function sectionsWord(n) { return ruPlural(n, "часть", "части", "частей"); }
  function minutesWord(n) { return ruPlural(n, "минута", "минуты", "минут"); }

  // ======================================================================
  // Band conversion tables (approximate, publicly published IELTS tables)
  // ======================================================================
  // Index = raw score (0-40) -> band (x.0 / x.5)
  const LISTENING_BAND_TABLE = [
    1,1,1,1,2,2.5,2.5,3,3,3.5,   // 0-9
    3.5,4,4,4.5,4.5,5,5,5.5,5.5,6, // 10-19
    6,6.5,6.5,6.5,7,7,7.5,7.5,8,8, // 20-29
    8,8.5,8.5,8.5,9,9,9,9,9,9,9,  // 30-40
  ];
  const READING_ACADEMIC_BAND_TABLE = [
    1,1,1,1,2,2.5,2.5,3,3,3.5,
    3.5,4,4,4.5,4.5,5,5,5.5,5.5,6,
    6,6.5,6.5,7,7,7,7.5,7.5,8,8,
    8,8.5,8.5,8.5,9,9,9,9,9,9,9,
  ];
  // General Training reading passages are considered less specialised than
  // Academic ones, so the same band requires a higher raw score in the
  // low-to-mid range; the two tables converge at the top end.
  const READING_GENERAL_BAND_TABLE = [
    1,1,1,1,2,2,2.5,2.5,2.5,3,
    3,3,3.5,3.5,3.5,4,4,4,4,4.5,
    4.5,4.5,4.5,5,5,5,5,5.5,5.5,5.5,
    6,6,6.5,6.5,7,7,7.5,8,8,8.5,9,
  ];
  function rawToBand(raw, table) {
    const idx = Math.max(0, Math.min(table.length - 1, Math.round(raw)));
    return table[idx];
  }

  // ======================================================================
  // Persistence
  // ======================================================================
  const PROGRESS_KEY = "ieltsmindset-progress-v1";
  function loadProgress() {
    try {
      const raw = localStorage.getItem(PROGRESS_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) { /* corrupt, fall through */ }
    return { history: [], streak: 0, lastActiveDate: null };
  }
  function saveProgress() {
    localStorage.setItem(PROGRESS_KEY, JSON.stringify(progress));
  }
  function recordResult(entry) {
    progress.history.unshift(entry);
    progress.history = progress.history.slice(0, 50);
    saveProgress();
  }
  function overallBand() {
    if (!progress.history.length) return null;
    const recent = progress.history.slice(0, 10);
    const avg = recent.reduce((s, h) => s + h.band, 0) / recent.length;
    return Math.round(avg * 2) / 2;
  }

  let progress = loadProgress();

  // ======================================================================
  // App state
  // ======================================================================
  const screenEl = document.getElementById("screen");
  let readingIndex = null;   // data/reading/index.json
  let listeningIndex = null; // data/listening/index.json
  let session = null;        // active practice/test session
  let timerInterval = null;

  // ======================================================================
  // Boot
  // ======================================================================
  async function boot() {
    wireTopbar();
    try {
      readingIndex = await fetchJson("data/reading/index.json");
    } catch (e) { readingIndex = { passages: [] }; }
    try {
      listeningIndex = await fetchJson("data/listening/index.json");
    } catch (e) { listeningIndex = { tests: [] }; }
    renderDashboard();
  }

  async function fetchJson(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`Failed to load ${path}`);
    return res.json();
  }

  function wireTopbar() {
    document.getElementById("brandBtn").addEventListener("click", () => { setNav("dashboard"); renderDashboard(); });
    document.querySelectorAll(".nav-link").forEach(btn => {
      btn.addEventListener("click", () => {
        const nav = btn.dataset.nav;
        setNav(nav);
        if (nav === "dashboard") renderDashboard();
        if (nav === "reading") renderHub("reading");
        if (nav === "listening") renderHub("listening");
      });
    });
    document.getElementById("soundToggle").addEventListener("click", (e) => {
      soundOn = !soundOn;
      e.currentTarget.textContent = soundOn ? "🔊" : "🔇";
      localStorage.setItem("ieltsmindset-sound", soundOn ? "1" : "0");
    });
    document.getElementById("exitConfirmCancel").addEventListener("click", hideExitConfirm);
    document.getElementById("exitConfirmLeave").addEventListener("click", () => {
      hideExitConfirm();
      stopTimer();
      if (session && session.skill === "listening") stopAudio();
      session = null;
      setNav("dashboard");
      renderDashboard();
    });
  }

  let soundOn = localStorage.getItem("ieltsmindset-sound") !== "0";
  document.getElementById("soundToggle").textContent = soundOn ? "🔊" : "🔇";

  function setNav(which) {
    document.querySelectorAll(".nav-link").forEach(b => b.classList.toggle("active", b.dataset.nav === which));
    document.getElementById("timerChip").classList.add("hidden");
  }

  function showExitConfirm() { document.getElementById("exitConfirmBackdrop").classList.remove("hidden"); }
  function hideExitConfirm() { document.getElementById("exitConfirmBackdrop").classList.add("hidden"); }

  // ======================================================================
  // Dashboard
  // ======================================================================
  function renderDashboard() {
    screenEl.classList.remove("full-bleed");
    const band = overallBand();
    const recent = progress.history.slice(0, 6);

    screenEl.innerHTML = `
      <div class="dash-hero">
        <div>
          <h1>${UI.dashboardTitle}</h1>
          <p>${UI.dashboardSub}</p>
        </div>
        ${band !== null ? `
          <div class="band-summary">
            <div class="band-num">${band.toFixed(1)}</div>
            <div><div class="band-label">${UI.overallBand}</div></div>
          </div>` : ""}
      </div>

      <div class="skill-grid">
        <div class="skill-card">
          <span class="skill-icon">📖</span>
          <h3>${UI.skillReading}</h3>
          <p>${UI.skillReadingDesc}</p>
          <div class="skill-actions">
            <button class="btn btn-ghost btn-sm" data-go="reading-practice">${UI.startPractice}</button>
            <button class="btn btn-primary btn-sm" data-go="reading-test">${UI.startTest}</button>
          </div>
        </div>
        <div class="skill-card">
          <span class="skill-icon">🎧</span>
          <h3>${UI.skillListening}</h3>
          <p>${UI.skillListeningDesc}</p>
          <div class="skill-actions">
            <button class="btn btn-ghost btn-sm" data-go="listening-practice">${UI.startPractice}</button>
            <button class="btn btn-primary btn-sm" data-go="listening-test">${UI.startTest}</button>
          </div>
        </div>
        <div class="skill-card locked">
          <span class="soon-badge">${UI.comingSoon}</span>
          <span class="skill-icon">✍️</span>
          <h3>${UI.skillWriting}</h3>
          <p>${UI.skillWritingDesc}</p>
        </div>
        <div class="skill-card locked">
          <span class="soon-badge">${UI.comingSoon}</span>
          <span class="skill-icon">🗣️</span>
          <h3>${UI.skillSpeaking}</h3>
          <p>${UI.skillSpeakingDesc}</p>
        </div>
      </div>

      <div class="section-title">${UI.recentTests} ${recent.length ? `<span class="count">(${progress.history.length})</span>` : ""}</div>
      ${recent.length ? `<div class="history-list">${recent.map(historyRowHtml).join("")}</div>`
        : `<div class="empty-state">${UI.noHistoryYet}</div>`}
    `;

    screenEl.querySelectorAll("[data-go]").forEach(btn => {
      btn.addEventListener("click", () => {
        const [skill] = btn.dataset.go.split("-");
        setNav(skill);
        renderHub(skill);
      });
    });
  }

  function historyRowHtml(h) {
    const icon = h.skill === "reading" ? "📖" : "🎧";
    const skillLabel = h.skill === "reading" ? UI.skillReading : UI.skillListening;
    const date = new Date(h.date).toLocaleDateString("ru-RU", { day: "numeric", month: "short" });
    return `
      <div class="history-row">
        <div class="h-skill">${icon}</div>
        <div>
          <div class="h-title">${skillLabel} · ${h.mode === "test" ? UI.testMode : UI.practiceMode}</div>
          <div class="h-meta">${date} · ${h.correct}/${h.total} ${UI.correctAnswers.toLowerCase()}</div>
        </div>
        <div class="h-band">${h.band.toFixed(1)}</div>
      </div>`;
  }

  // ======================================================================
  // Hub (per-skill: choose practice content or full test)
  // ======================================================================
  function renderHub(skill) {
    screenEl.classList.remove("full-bleed");
    const isReading = skill === "reading";
    const items = isReading ? (readingIndex.passages || []) : (listeningIndex.tests || []);
    const testGroups = groupByTestGroup(items);

    screenEl.innerHTML = `
      <div class="hub-header">
        <h1>${isReading ? UI.skillReading : UI.skillListening}</h1>
        <p>${isReading ? UI.skillReadingDesc : UI.skillListeningDesc}</p>
      </div>
      <div class="section-title">${UI.testMode} <span class="count">(${testGroups.length})</span></div>
      <div class="content-list" style="margin-bottom:28px;">
        ${testGroups.length ? testGroups.map((g, i) => testGroupRowHtml(g, i, isReading)).join("")
          : `<div class="empty-state">Полные тесты пока не собраны.</div>`}
      </div>
      <div class="section-title">${isReading ? "Отдельные тексты" : "Отдельные записи"} · ${UI.practiceMode} <span class="count">(${items.length})</span></div>
      <div class="content-list" id="contentList">
        ${items.length ? items.map((it, i) => contentRowHtml(it, i, isReading)).join("") : `<div class="empty-state">Материалы пока не добавлены.</div>`}
      </div>
    `;

    screenEl.querySelectorAll("[data-testgroup]").forEach(row => {
      row.addEventListener("click", () => startFullTest(skill, row.dataset.testgroup));
    });
    screenEl.querySelectorAll("[data-practice-idx]").forEach(row => {
      row.addEventListener("click", () => {
        const idx = Number(row.dataset.practiceIdx);
        startPractice(skill, idx);
      });
    });
  }

  function groupByTestGroup(items) {
    const map = new Map();
    items.forEach(it => {
      const g = it.testGroup || "1";
      if (!map.has(g)) map.set(g, []);
      map.get(g).push(it);
    });
    return Array.from(map.entries()).map(([id, list]) => ({ id, items: list }));
  }

  function testGroupRowHtml(group, idx, isReading) {
    const qCount = group.items.reduce((s, it) => s + (it.questionGroups || []).reduce((s2, g) => s2 + g.questions.length, 0), 0);
    const unitCount = group.items.length;
    const unitLabel = isReading ? `${unitCount} ${passagesWord(unitCount)}` : `${unitCount} ${sectionsWord(unitCount)}`;
    const isGeneral = isReading && group.items[0]?.testType === "general";
    const moduleTag = isReading ? ` <span class="module-tag">${isGeneral ? UI.moduleGeneral : UI.moduleAcademic}</span>` : "";
    return `
      <div class="content-row" data-testgroup="${group.id}">
        <span class="c-badge">${UI.testShort} ${idx + 1}</span>
        <span class="c-title">${isReading ? "Полный тест по чтению" : "Полный тест по аудированию"} — ${unitLabel}, ${qCount} ${questionsWord(qCount)}${moduleTag}</span>
        <span class="c-status">⏱ ${isReading ? "60 мин" : "~30 мин"}</span>
      </div>`;
  }

  function contentRowHtml(item, idx, isReading) {
    const qCount = (item.questionGroups || []).reduce((s, g) => s + g.questions.length, 0);
    const tg = item.testGroup || "1";
    const badge = isReading
      ? `${UI.passage} · ${UI.testShort} ${tg}`
      : `${UI.section} ${item.sectionNumber || idx + 1} · ${UI.testShort} ${tg}`;
    const moduleTag = isReading && item.testType === "general"
      ? ` <span class="module-tag">${UI.moduleGeneral}</span>` : "";
    return `
      <div class="content-row" data-practice-idx="${idx}">
        <span class="c-badge">${badge}</span>
        <span class="c-title">${item.title}${moduleTag}</span>
        <span class="c-meta">${qCount} ${questionsWord(qCount)}</span>
      </div>`;
  }

  // ======================================================================
  // Session builders
  // ======================================================================
  function startPractice(skill, idx) {
    const items = skill === "reading" ? readingIndex.passages : listeningIndex.tests;
    const content = [items[idx]];
    beginSession(skill, "practice", content);
  }

  function startFullTest(skill, testGroupId) {
    setNav(skill);
    const items = skill === "reading" ? (readingIndex.passages || []) : (listeningIndex.tests || []);
    const groupId = testGroupId || (items[0] && (items[0].testGroup || "1"));
    const content = items.filter(it => (it.testGroup || "1") === groupId);
    if (!content.length) { renderHub(skill); return; }
    beginSession(skill, "test", content);
  }

  function beginSession(skill, mode, content) {
    const allQuestions = [];
    content.forEach((c, ci) => {
      (c.questionGroups || []).forEach(g => {
        g.questions.forEach(q => allQuestions.push({ ...q, groupType: g.type, contentIndex: ci }));
      });
    });
    session = {
      skill, mode, content,
      currentContentIndex: 0,
      answers: {},
      flagged: new Set(),
      allQuestions,
      startedAt: Date.now(),
      remainingSeconds: skill === "reading" ? READING_TEST_SECONDS : null,
      audioEl: null,
      audioSectionDone: {},
    };
    if (skill === "reading") {
      renderReadingShell();
      if (mode === "test") startTimer();
    } else {
      renderListeningShell();
    }
  }

  // ======================================================================
  // Timer
  // ======================================================================
  function startTimer() {
    const chip = document.getElementById("timerChip");
    chip.classList.remove("hidden");
    updateTimerDisplay();
    timerInterval = setInterval(() => {
      session.remainingSeconds--;
      updateTimerDisplay();
      if (session.remainingSeconds <= 0) {
        stopTimer();
        submitTest(true);
      }
    }, 1000);
  }
  function stopTimer() {
    clearInterval(timerInterval);
    timerInterval = null;
    document.getElementById("timerChip").classList.add("hidden");
  }
  function updateTimerDisplay() {
    const s = Math.max(0, session.remainingSeconds);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    document.getElementById("timerText").textContent = `${m}:${String(sec).padStart(2, "0")}`;
    document.getElementById("timerChip").classList.toggle("low-time", s <= 300);
  }

  // ======================================================================
  // Reading shell
  // ======================================================================
  function renderReadingShell() {
    screenEl.classList.add("full-bleed");
    const content = session.content[session.currentContentIndex];
    screenEl.innerHTML = `
      <div class="test-shell">
        <div class="test-topbar">
          <span class="part-label">${UI.passage} ${session.currentContentIndex + 1}${session.content.length > 1 ? ` / ${session.content.length}` : ""}: ${content.title}</span>
          <span class="part-instructions">${session.mode === "test" ? UI.testMode : UI.practiceMode}</span>
          <button class="btn btn-ghost btn-sm" id="exitBtn">${UI.exitTest}</button>
        </div>
        <div class="test-split">
          <div class="pane pane-passage" id="passagePane"></div>
          <div class="pane pane-questions" id="questionsPane"></div>
        </div>
        <div class="palette-bar" id="paletteBar"></div>
      </div>
    `;
    renderPassagePane(content);
    renderQuestionsPane(content);
    renderPalette();
    document.getElementById("exitBtn").addEventListener("click", onExitClicked);
  }

  function renderPassagePane(content) {
    const pane = document.getElementById("passagePane");
    pane.innerHTML = `
      <h2>${content.title}</h2>
      ${(content.paragraphs || []).map(p => `<p>${p.label ? `<span class="p-label">${p.label}</span>` : ""}${p.text}</p>`).join("")}
    `;
  }

  function renderQuestionsPane(content) {
    const pane = document.getElementById("questionsPane");
    pane.innerHTML = (content.questionGroups || []).map(g => renderQuestionGroup(g)).join("");
    wireQuestionInputs(pane);
  }

  // ======================================================================
  // Question group rendering (shared by Reading + Listening)
  // ======================================================================
  function renderQuestionGroup(group) {
    const nums = group.questions.map(q => q.number);
    const range = nums.length > 1 ? `${nums[0]}–${nums[nums.length - 1]}` : `${nums[0]}`;
    let body = "";
    switch (group.type) {
      case "multiple-choice": body = group.questions.map(q => renderMCQuestion(q)).join(""); break;
      case "true-false-not-given": body = group.questions.map(q => renderTFNGQuestion(q, "trueFalse")).join(""); break;
      case "yes-no-not-given": body = group.questions.map(q => renderTFNGQuestion(q, "yesNo")).join(""); break;
      case "matching-headings": body = renderMatchingHeadingsGroup(group); break;
      case "matching-information":
      case "matching-features": body = group.questions.map(q => renderMatchingQuestion(q, group)).join(""); break;
      case "sentence-completion":
      case "short-answer": body = group.questions.map(q => renderCompletionQuestion(q, group)).join(""); break;
      case "summary-completion": body = renderSummaryCompletion(group); break;
      case "table-completion": body = renderTableCompletion(group); break;
      case "diagram-label-completion": body = group.questions.map(q => renderCompletionQuestion(q, group)).join(""); break;
      default: body = `<p>Unsupported question type: ${group.type}</p>`;
    }
    return `
      <div class="qgroup" data-group-type="${group.type}">
        <div class="qgroup-range">${UI.questions} ${range}</div>
        <div class="qgroup-instructions"><b>${group.instructions}</b></div>
        ${body}
      </div>`;
  }

  function renderMCQuestion(q) {
    const multi = Array.isArray(q.answer);
    const inputType = multi ? "checkbox" : "radio";
    return `
      <div class="qitem" id="q${q.number}" data-qnum="${q.number}">
        <div class="qstatement"><span class="qnum">${q.number}</span>${q.statement || q.prompt || ""}</div>
        <div class="opt-row">
          ${q.options.map((opt, i) => `
            <label class="opt-choice" data-optidx="${i}">
              <input type="${inputType}" name="q${q.number}" value="${i}" />
              <span>${String.fromCharCode(65 + i)}. ${opt}</span>
            </label>`).join("")}
        </div>
      </div>`;
  }

  function renderTFNGQuestion(q, kind) {
    const options = kind === "yesNo" ? UI.yesNoOptions : UI.trueFalseOptions;
    const labels = kind === "yesNo" ? UI.yesNoLabelsRu : UI.trueFalseLabelsRu;
    return `
      <div class="qitem" id="q${q.number}" data-qnum="${q.number}">
        <div class="qstatement"><span class="qnum">${q.number}</span>${q.statement}</div>
        <div class="tfng-row">
          ${options.map(opt => `<button type="button" class="tfng-btn" data-value="${opt}">${opt} <br><small>${labels[opt]}</small></button>`).join("")}
        </div>
      </div>`;
  }

  function renderMatchingHeadingsGroup(group) {
    const bank = `
      <div class="heading-bank">
        <b>Список заголовков</b>
        <ol type="i">${group.headingOptions.map(h => `<li>${h}</li>`).join("")}</ol>
      </div>`;
    const items = group.questions.map(q => `
      <div class="qitem" id="q${q.number}" data-qnum="${q.number}">
        <div class="qstatement"><span class="qnum">${q.number}</span>${UI.passage} ${q.paragraphLabel ? `— параграф <b>${q.paragraphLabel}</b>` : ""}</div>
        <select class="match-select" data-qnum="${q.number}">
          <option value="">—</option>
          ${group.headingOptions.map((h, i) => `<option value="${i}">${romanNumeral(i + 1)}. ${h}</option>`).join("")}
        </select>
      </div>`).join("");
    return bank + items;
  }

  function renderMatchingQuestion(q, group) {
    const opts = group.matchOptions || group.headingOptions || [];
    return `
      <div class="qitem" id="q${q.number}" data-qnum="${q.number}">
        <div class="qstatement"><span class="qnum">${q.number}</span>${q.statement}</div>
        <select class="match-select" data-qnum="${q.number}">
          <option value="">—</option>
          ${opts.map((o, i) => `<option value="${typeof o === "string" ? o : i}">${typeof o === "string" ? o : o.label}</option>`).join("")}
        </select>
      </div>`;
  }

  function renderCompletionQuestion(q, group) {
    const limit = group.wordLimit ? `<div class="qgroup-range" style="margin-top:2px">${UI.wordLimitWarn(group.wordLimit)}</div>` : "";
    const prompt = q.prompt || "";
    const inputHtml = `<input type="text" class="blank-input" data-qnum="${q.number}" autocomplete="off" />`;
    const line = prompt.includes("___") ? prompt.replace("___", inputHtml) : `${prompt} ${inputHtml}`;
    return `
      <div class="qitem" id="q${q.number}" data-qnum="${q.number}">
        <div class="qstatement"><span class="qnum">${q.number}</span>${line}</div>
        ${limit}
      </div>`;
  }

  function renderSummaryCompletion(group) {
    const bank = group.wordBank ? `
      <div class="heading-bank"><b>Банк слов</b><br>${group.wordBank.join(" · ")}</div>` : "";
    const limitLine = group.wordLimit ? `<div class="qgroup-range">${UI.wordLimitWarn(group.wordLimit)}</div>` : "";
    const text = group.summaryText || group.questions.map(q => q.prompt).join(" ");
    let rendered = text;
    group.questions.forEach(q => {
      rendered = rendered.replace(`___${q.number}___`, `<span class="qnum">${q.number}</span><input type="text" class="blank-input" data-qnum="${q.number}" autocomplete="off" />`);
    });
    return `${bank}${limitLine}<div class="completion-line">${rendered}</div>`;
  }

  function renderTableCompletion(group) {
    if (!group.table) return group.questions.map(q => renderCompletionQuestion(q, group)).join("");
    const limitLine = group.wordLimit ? `<div class="qgroup-range">${UI.wordLimitWarn(group.wordLimit)}</div>` : "";
    const rows = group.table.rows.map(row => `
      <tr>${row.map(cell => {
        if (cell && typeof cell === "object" && cell.qnum) {
          return `<td>${cell.before || ""}<span class="qnum">${cell.qnum}</span><input type="text" class="blank-input" data-qnum="${cell.qnum}" autocomplete="off" />${cell.after || ""}</td>`;
        }
        return `<td>${cell}</td>`;
      }).join("")}</tr>`).join("");
    return `${limitLine}<div class="table-wrap"><table class="q-table">
      <thead><tr>${group.table.headers.map(h => `<th>${h}</th>`).join("")}</tr></thead>
      <tbody>${rows}</tbody>
    </table></div>`;
  }

  function romanNumeral(n) {
    const map = ["i","ii","iii","iv","v","vi","vii","viii","ix","x","xi","xii","xiii","xiv","xv"];
    return map[n - 1] || String(n);
  }

  // ======================================================================
  // Wiring question inputs -> session.answers
  // ======================================================================
  function wireQuestionInputs(root) {
    root.querySelectorAll('.opt-choice input[type="radio"]').forEach(inp => {
      inp.addEventListener("change", () => {
        const qnum = Number(inp.name.slice(1));
        session.answers[qnum] = Number(inp.value);
        const item = document.getElementById(`q${qnum}`);
        item.querySelectorAll(".opt-choice").forEach(l => l.classList.remove("selected"));
        inp.closest(".opt-choice").classList.add("selected");
        onAnswerChanged(qnum);
      });
    });
    root.querySelectorAll('.opt-choice input[type="checkbox"]').forEach(inp => {
      inp.addEventListener("change", () => {
        const qnum = Number(inp.name.slice(1));
        const item = document.getElementById(`q${qnum}`);
        const checked = Array.from(item.querySelectorAll('input[type="checkbox"]:checked')).map(c => Number(c.value));
        session.answers[qnum] = checked;
        inp.closest(".opt-choice").classList.toggle("selected", inp.checked);
        onAnswerChanged(qnum);
      });
    });
    root.querySelectorAll(".tfng-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const item = btn.closest(".qitem");
        const qnum = Number(item.dataset.qnum);
        session.answers[qnum] = btn.dataset.value;
        item.querySelectorAll(".tfng-btn").forEach(b => b.classList.remove("selected"));
        btn.classList.add("selected");
        onAnswerChanged(qnum);
      });
    });
    root.querySelectorAll(".match-select").forEach(sel => {
      sel.addEventListener("change", () => {
        const qnum = Number(sel.dataset.qnum);
        session.answers[qnum] = sel.value;
        sel.classList.toggle("answered", sel.value !== "");
        onAnswerChanged(qnum);
      });
    });
    root.querySelectorAll(".blank-input").forEach(inp => {
      inp.addEventListener("input", () => {
        const qnum = Number(inp.dataset.qnum);
        session.answers[qnum] = inp.value;
        inp.classList.toggle("answered", inp.value.trim() !== "");
        onAnswerChanged(qnum, false);
      });
    });
  }

  function onAnswerChanged(qnum, refreshPalette = true) {
    if (refreshPalette) renderPalette();
    else updatePaletteCell(qnum);
  }

  // ======================================================================
  // Palette
  // ======================================================================
  function renderPalette() {
    const bar = document.getElementById("paletteBar");
    if (!bar) return;
    const groups = {};
    session.content.forEach((c, ci) => { groups[ci] = []; });
    session.allQuestions.forEach(q => groups[q.contentIndex].push(q.number));

    let html = "";
    Object.keys(groups).forEach(ci => {
      const label = session.skill === "reading" ? `${UI.passage} ${Number(ci) + 1}` : `${UI.section} ${Number(ci) + 1}`;
      html += `<span class="palette-section-label">${label}</span><div class="palette-grid">`;
      groups[ci].forEach(n => {
        html += paletteCellHtml(n);
      });
      html += `</div>`;
    });
    html += `
      <div class="palette-actions">
        <button class="btn btn-ghost btn-sm" id="flagCurrentBtn">${UI.flagQuestion}</button>
        <button class="btn btn-gold btn-sm" id="submitTestBtn">${UI.submitTest}</button>
      </div>`;
    bar.innerHTML = html;

    bar.querySelectorAll(".palette-cell").forEach(cell => {
      cell.addEventListener("click", () => jumpToQuestion(Number(cell.dataset.qnum)));
    });
    document.getElementById("submitTestBtn").addEventListener("click", () => confirmSubmit());
    const flagBtn = document.getElementById("flagCurrentBtn");
    if (flagBtn) flagBtn.addEventListener("click", toggleFlagCurrent);
  }

  function paletteCellHtml(n) {
    const answered = session.answers[n] !== undefined && session.answers[n] !== "" &&
      !(Array.isArray(session.answers[n]) && session.answers[n].length === 0);
    const flagged = session.flagged.has(n);
    return `<button type="button" class="palette-cell ${answered ? "answered" : ""} ${flagged ? "flagged" : ""}" data-qnum="${n}">${n}</button>`;
  }

  function updatePaletteCell(qnum) {
    const bar = document.getElementById("paletteBar");
    if (!bar) return;
    const cell = bar.querySelector(`.palette-cell[data-qnum="${qnum}"]`);
    if (!cell) return;
    const answered = session.answers[qnum] !== undefined && session.answers[qnum] !== "";
    cell.classList.toggle("answered", answered);
  }

  function jumpToQuestion(qnum) {
    const q = session.allQuestions.find(x => x.number === qnum);
    if (!q) return;
    if (q.contentIndex !== session.currentContentIndex) {
      session.currentContentIndex = q.contentIndex;
      if (session.skill === "reading") {
        renderReadingShell();
      } else {
        renderListeningSectionView();
      }
    }
    const el = document.getElementById(`q${qnum}`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
      el.classList.add("flagged-flash");
    }
  }

  function toggleFlagCurrent() {
    // flags the first visible question in the current pane as a simple affordance
    const pane = document.getElementById("questionsPane");
    if (!pane) return;
    const firstItem = pane.querySelector(".qitem");
    if (!firstItem) return;
    const qnum = Number(firstItem.dataset.qnum);
    if (session.flagged.has(qnum)) session.flagged.delete(qnum);
    else session.flagged.add(qnum);
    renderPalette();
  }

  function onExitClicked() {
    if (session.mode === "test") showExitConfirm();
    else {
      stopTimer();
      if (session.skill === "listening") stopAudio();
      session = null;
      renderHub(document.querySelector(".nav-link.active")?.dataset.nav || "reading");
    }
  }

  // ======================================================================
  // Grading
  // ======================================================================
  function normalizeText(s) {
    return String(s || "").trim().toLowerCase().replace(/[.,!?;:'"]/g, "").replace(/\s+/g, " ");
  }

  function gradeQuestion(q) {
    const user = session.answers[q.number];
    if (user === undefined || user === "" || (Array.isArray(user) && user.length === 0)) return false;
    switch (q.groupType) {
      case "multiple-choice":
        if (Array.isArray(q.answer)) {
          const a = [...q.answer].sort();
          const u = [...(Array.isArray(user) ? user : [user])].sort();
          return a.length === u.length && a.every((v, i) => v === u[i]);
        }
        return Number(user) === Number(q.answer);
      case "true-false-not-given":
      case "yes-no-not-given":
        return String(user).toUpperCase() === String(q.answer).toUpperCase();
      case "matching-headings":
        return Number(user) === Number(q.answer);
      case "matching-information":
      case "matching-features":
        return normalizeText(user) === normalizeText(q.answer);
      case "sentence-completion":
      case "summary-completion":
      case "short-answer":
      case "table-completion":
      case "diagram-label-completion": {
        const accepted = Array.isArray(q.answer) ? q.answer : [q.answer];
        return accepted.some(a => normalizeText(a) === normalizeText(user));
      }
      default:
        return false;
    }
  }

  function displayAnswer(q, value) {
    if (value === undefined || value === "") return "—";
    switch (q.groupType) {
      case "multiple-choice": {
        const idxs = Array.isArray(value) ? value : [value];
        return idxs.map(i => `${String.fromCharCode(65 + Number(i))}`).join(", ");
      }
      case "matching-headings":
        return romanNumeral(Number(value) + 1).toUpperCase();
      default:
        return String(value);
    }
  }
  function correctAnswerDisplay(q) {
    switch (q.groupType) {
      case "multiple-choice": {
        const idxs = Array.isArray(q.answer) ? q.answer : [q.answer];
        return idxs.map(i => String.fromCharCode(65 + Number(i))).join(", ");
      }
      case "matching-headings":
        return romanNumeral(Number(q.answer) + 1).toUpperCase();
      case "sentence-completion":
      case "summary-completion":
      case "short-answer":
      case "table-completion":
      case "diagram-label-completion":
        return Array.isArray(q.answer) ? q.answer[0] : q.answer;
      default:
        return String(q.answer);
    }
  }

  // ======================================================================
  // Submit / results
  // ======================================================================
  function confirmSubmit() {
    const total = session.allQuestions.length;
    const answered = session.allQuestions.filter(q => {
      const v = session.answers[q.number];
      return v !== undefined && v !== "" && !(Array.isArray(v) && v.length === 0);
    }).length;
    screenEl.insertAdjacentHTML("beforeend", `
      <div class="modal-backdrop" id="submitConfirmBackdrop">
        <div class="modal-box">
          <h3>${UI.submitConfirmTitle}</h3>
          <p>${answered < total ? `${UI.submitConfirmBody} (${answered}/${total})` : UI.submitConfirmBodyAll}</p>
          <div class="modal-actions">
            <button class="btn btn-ghost" id="submitCancelBtn">${UI.cancel}</button>
            <button class="btn btn-primary" id="submitConfirmBtn">${UI.confirmSubmit}</button>
          </div>
        </div>
      </div>`);
    document.getElementById("submitCancelBtn").addEventListener("click", () => {
      document.getElementById("submitConfirmBackdrop").remove();
    });
    document.getElementById("submitConfirmBtn").addEventListener("click", () => {
      document.getElementById("submitConfirmBackdrop").remove();
      submitTest(false);
    });
  }

  function submitTest(autoSubmitted) {
    stopTimer();
    if (session.skill === "listening") stopAudio();
    const total = session.allQuestions.length;
    let correct = 0;
    session.allQuestions.forEach(q => { if (gradeQuestion(q)) correct++; });
    const isGeneralReading = session.skill === "reading" && session.content[0]?.testType === "general";
    const table = session.skill === "reading"
      ? (isGeneralReading ? READING_GENERAL_BAND_TABLE : READING_ACADEMIC_BAND_TABLE)
      : LISTENING_BAND_TABLE;
    const band = rawToBand(correct, table);
    const elapsedMs = Date.now() - session.startedAt;

    const entry = {
      skill: session.skill, mode: session.mode, date: Date.now(),
      correct, total, band, elapsedMs, autoSubmitted,
    };
    recordResult(entry);
    renderResults(entry);
  }

  function renderResults(entry) {
    screenEl.classList.remove("full-bleed");
    const minutes = Math.round(entry.elapsedMs / 60000);
    screenEl.innerHTML = `
      <div class="results-hero">
        <div class="results-band">
          <div class="num">${entry.band.toFixed(1)}</div>
          <div class="lbl">${UI.yourBand}</div>
        </div>
        <div class="results-stats">
          <div class="results-stat"><div class="n">${entry.correct} / ${entry.total}</div><div class="l">${UI.correctAnswers}</div></div>
          <div class="results-stat"><div class="n">${minutes} мин</div><div class="l">${UI.timeTaken}</div></div>
        </div>
      </div>
      <div class="section-title">${UI.reviewTitle}</div>
      <div id="reviewList">
        ${session.allQuestions.map(q => reviewItemHtml(q)).join("")}
      </div>
      <div class="skill-actions" style="margin-top:24px; display:flex; gap:10px;">
        <button class="btn btn-primary" id="backHomeBtn">${UI.backToDashboard}</button>
      </div>
    `;
    document.getElementById("backHomeBtn").addEventListener("click", () => {
      session = null;
      setNav("dashboard");
      renderDashboard();
    });
  }

  function reviewItemHtml(q) {
    const ok = gradeQuestion(q);
    const userVal = session.answers[q.number];
    return `
      <div class="review-item ${ok ? "correct" : "incorrect"}">
        <div class="r-q"><span class="qnum">${q.number}</span>${q.statement || q.prompt || ""}</div>
        ${!ok ? `<div class="r-your">${UI.yourAnswer}: ${displayAnswer(q, userVal)}</div>` : ""}
        <div class="r-correct">${UI.correctAnswer}: ${correctAnswerDisplay(q)}</div>
      </div>`;
  }

  // ======================================================================
  // Listening shell (reuses question-group rendering; adds audio player)
  // ======================================================================
  function renderListeningShell() {
    renderListeningSectionView();
    if (session.mode === "test") session.remainingSeconds = null; // listening timing is audio-driven, not a wall clock
  }

  function renderListeningSectionView() {
    screenEl.classList.add("full-bleed");
    const content = session.content[session.currentContentIndex];
    screenEl.innerHTML = `
      <div class="test-shell">
        <div class="test-topbar">
          <span class="part-label">${UI.section} ${session.currentContentIndex + 1}${session.content.length > 1 ? ` / ${session.content.length}` : ""}: ${content.title}</span>
          <span class="part-instructions">${session.mode === "test" ? UI.testMode : UI.practiceMode}</span>
          <button class="btn btn-ghost btn-sm" id="exitBtn">${UI.exitTest}</button>
        </div>
        <div class="pane" style="max-width:900px; margin:0 auto; width:100%;">
          <div class="audio-player" id="audioPlayer">
            <button class="ap-play" id="apPlayBtn">▶</button>
            <span class="ap-section">${UI.section} ${session.currentContentIndex + 1}</span>
            <div class="ap-progress"><div class="ap-progress-fill" id="apProgressFill"></div></div>
            <span class="ap-time" id="apTime">0:00 / 0:00</span>
          </div>
          <div id="questionsPane"></div>
        </div>
        <div class="palette-bar" id="paletteBar"></div>
      </div>
    `;
    renderQuestionsPane(content);
    renderPalette();
    document.getElementById("exitBtn").addEventListener("click", onExitClicked);
    setupAudio(content);
  }

  function setupAudio(content) {
    stopAudio();
    const player = document.getElementById("audioPlayer");
    const playBtn = document.getElementById("apPlayBtn");
    const fill = document.getElementById("apProgressFill");
    const timeEl = document.getElementById("apTime");

    if (content.audioFile) {
      const audio = new Audio(content.audioFile);
      session.audioEl = audio;
      playBtn.addEventListener("click", () => {
        if (audio.paused) { audio.play(); playBtn.textContent = "❚❚"; }
        else { audio.pause(); playBtn.textContent = "▶"; }
      });
      audio.addEventListener("timeupdate", () => {
        if (!audio.duration) return;
        fill.style.width = `${(audio.currentTime / audio.duration) * 100}%`;
        timeEl.textContent = `${fmtTime(audio.currentTime)} / ${fmtTime(audio.duration)}`;
      });
      audio.addEventListener("ended", () => { playBtn.textContent = "▶"; onSectionAudioEnded(); });
    } else {
      // Fallback: no audio file yet — browser speech synthesis reads the transcript (practice quality only).
      playBtn.addEventListener("click", () => speakTranscriptFallback(content, playBtn, fill, timeEl));
      timeEl.textContent = "TTS (черновой режим)";
    }
  }

  function fmtTime(s) {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${String(sec).padStart(2, "0")}`;
  }

  let _fallbackSpeaking = false;
  function speakTranscriptFallback(content, playBtn, fill, timeEl) {
    if (!("speechSynthesis" in window)) return;
    if (_fallbackSpeaking) {
      window.speechSynthesis.cancel();
      _fallbackSpeaking = false;
      playBtn.textContent = "▶";
      return;
    }
    const lines = content.transcript || [];
    if (!lines.length) return;
    _fallbackSpeaking = true;
    playBtn.textContent = "❚❚";
    let i = 0;
    const speakNext = () => {
      if (!_fallbackSpeaking || i >= lines.length) {
        _fallbackSpeaking = false;
        playBtn.textContent = "▶";
        fill.style.width = "100%";
        onSectionAudioEnded();
        return;
      }
      fill.style.width = `${Math.round((i / lines.length) * 100)}%`;
      timeEl.textContent = `${i + 1} / ${lines.length}`;
      const utter = new SpeechSynthesisUtterance(lines[i].text);
      utter.rate = 0.98;
      utter.onend = () => { i++; speakNext(); };
      utter.onerror = () => { i++; speakNext(); };
      window.speechSynthesis.speak(utter);
    };
    speakNext();
  }

  function stopAudio() {
    if (session && session.audioEl) { session.audioEl.pause(); session.audioEl = null; }
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    _fallbackSpeaking = false;
  }

  function onSectionAudioEnded() {
    if (!session) return;
    session.audioSectionDone[session.currentContentIndex] = true;
    if (session.mode === "test" && session.currentContentIndex < session.content.length - 1) {
      const bar = document.getElementById("paletteBar");
      if (bar && !document.getElementById("nextSectionBtn")) {
        bar.insertAdjacentHTML("beforeend", `<button class="btn btn-gold btn-sm" id="nextSectionBtn" style="margin-left:8px;">${UI.nextSection}</button>`);
        document.getElementById("nextSectionBtn").addEventListener("click", () => {
          session.currentContentIndex++;
          renderListeningSectionView();
        });
      }
    }
  }

  boot();
})();
