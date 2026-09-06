/* app.js — shell + chat assistant view.
   Talks to the real integrated backend: POST /api/query, POST /api/classify,
   GET /api/health. No mocked data anywhere. */
"use strict";

const App = (() => {
  const state = {
    jurisdiction: "India",
    language: "en",
    formulationClass: null,
    history: [],          // {role, content} — capped, sent with each request
    busy: false,
  };

  const SCENARIOS = {
    "classical-patent": {
      query: "Can I patent a classical Ayurvedic formulation from an authoritative text?",
      jurisdiction: "India",
    },
    "abs": {
      query: "I want to commercialise a formulation using a plant collected in India — what approvals do I need?",
      jurisdiction: "India",
    },
    "gi": {
      query: "How do I register a GI tag for an Ayurvedic product tied to a region?",
      jurisdiction: "India",
    },
    "international-patent": {
      query: "I want to file a patent for a new Ayurvedic drug outside India — what route do I use?",
      jurisdiction: "International",
    },
  };

  const CLASSIFIER_EXAMPLE = {
    primary_purpose: "therapeutic",
    text_source: "yes",
    standardised_fraction: "no",
    ingredients_known: "yes",
    new_indication: "no",
  };

  const el = (id) => document.getElementById(id);
  const els = {
    conversation: () => el("conversation"),
    input: () => el("queryInput"),
    sendBtn: () => el("sendBtn"),
    composer: () => el("composer"),
    sourcesList: () => el("sourcesList"),
    sourcesEmpty: () => document.querySelector(".sources-empty"),
    metaList: () => el("metaList"),
    metaEmpty: () => document.querySelector("#metaCard .meta-empty"),
    specialistList: () => el("specialistList"),
    healthDot: () => el("healthDot"),
    healthText: () => el("healthText"),
    jurisdictionNote: () => el("jurisdictionNote"),
    welcome: () => el("welcome"),
    newChatBtn: () => el("newChatBtn"),
  };

  function esc(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  /* ── shell: navigation, toggles, health ─────────────────────────── */

  const VIEW_HINTS = {
    chat: "chatHint",
    classifier: "classifierHint",
    about: "aboutHint",
    help: "helpHint",
  };

  function switchView(view) {
    ["chat", "classifier", "about", "help"].forEach((name) => {
      document.getElementById(`view-${name}`).classList.toggle("hidden", name !== view);
    });
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.classList.toggle("active", item.dataset.view === view);
    });
    const titleKey = view === "chat" ? "navChat"
      : view === "classifier" ? "navClassifier"
      : view === "about" ? "navAbout" : "navHelp";
    el("viewTitle").textContent = I18N.t(titleKey);
    el("viewHint").textContent = I18N.t(VIEW_HINTS[view]);
    if (view === "classifier") Classifier.show();
  }

  function updateJurisdictionNote() {
    const note = els.jurisdictionNote();
    note.textContent = state.jurisdiction === "India"
      ? I18N.t("jurisdictionNoteIndia")
      : I18N.t("jurisdictionNoteIntl");
    note.classList.add("visible");
  }

  function initShell() {
    document.querySelectorAll(".nav-item").forEach((item) => {
      item.addEventListener("click", () => switchView(item.dataset.view));
    });

    el("jurisdictionToggle").addEventListener("click", (event) => {
      const button = event.target.closest(".seg");
      if (!button) return;
      state.jurisdiction = button.dataset.value;
      document.querySelectorAll("#jurisdictionToggle .seg").forEach((s) =>
        s.classList.toggle("active", s === button));
      updateJurisdictionNote();
    });

    el("languageToggle").addEventListener("click", (event) => {
      const button = event.target.closest(".seg");
      if (!button) return;
      state.language = button.dataset.value;
      document.querySelectorAll("#languageToggle .seg").forEach((s) =>
        s.classList.toggle("active", s === button));
      I18N.apply(state.language);
    });

    el("formulationSelect").addEventListener("change", (event) => {
      state.formulationClass = event.target.value || null;
    });

    els.newChatBtn().addEventListener("click", () => {
      state.history = [];
      els.conversation().innerHTML = "";
      els.conversation().appendChild(buildWelcome());
      els.sourcesList().innerHTML = "";
      els.sourcesEmpty().classList.remove("hidden");
      setMeta(null);
      els.newChatBtn().classList.add("hidden");
    });

    document.addEventListener("i18n:changed", updateJurisdictionNote);
    updateJurisdictionNote();
  }

  async function refreshHealth() {
    try {
      const health = await API.health();
      els.healthDot().className = "health-dot ok";
      els.healthText().textContent = I18N.t("healthOk");
      const names = {
        INDIA_IP: "specIndia",
        ABS_TK: "specAbs",
        INTERNATIONAL_IP: "specIntl",
        CLASSIFICATION: "specCls",
      };
      const items = Object.keys(health.specialists || {}).map((domain) => `
        <li><svg class="icon"><use href="#i-check"/></svg><span>${esc(I18N.t(names[domain] || domain))}</span></li>`);
      items.push(`<li><svg class="icon"><use href="#i-check"/></svg><span>${esc(I18N.t("specCentral"))}</span></li>`);
      els.specialistList().innerHTML = items.join("");
    } catch (err) {
      els.healthDot().className = "health-dot down";
      els.healthText().textContent = I18N.t("healthDown");
      els.specialistList().innerHTML = `<li class="muted">${esc(I18N.t("healthDown"))}</li>`;
    }
  }

  /* ── conversation ───────────────────────────────────────────────── */

  function buildWelcome() {
    const node = document.createElement("div");
    node.className = "welcome";
    node.id = "welcome";
    node.innerHTML = `
      <svg class="icon icon-xl"><use href="#i-mark"/></svg>
      <h2>${esc(I18N.t("welcomeTitle"))}</h2>
      <p>${esc(I18N.t("welcomeSub"))}</p>`;
    return node;
  }

  function addUserMessage(text) {
    els.welcome() && els.welcome().remove();
    els.newChatBtn().classList.remove("hidden");
    const row = document.createElement("div");
    row.className = "msg msg-user";
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    row.appendChild(bubble);
    els.conversation().appendChild(row);
  }

  function addAssistantShell() {
    const row = document.createElement("div");
    row.className = "msg msg-assistant";
    row.innerHTML = `
      <div class="answer-card">
        <div class="answer-head"><svg class="icon icon-sm"><use href="#i-mark"/></svg><span>IP-SAKTI Sahayak</span></div>
        <div class="answer-body"><p class="muted"><span class="typing"><i></i><i></i><i></i></span></p></div>
      </div>`;
    els.conversation().appendChild(row);
    els.conversation().scrollTop = els.conversation().scrollHeight;
    return {
      card: row.querySelector(".answer-card"),
      body: row.querySelector(".answer-body"),
    };
  }

  function answerParagraphs(text) {
    const container = document.createElement("div");
    String(text || "").split(/\n{2,}/).forEach((block) => {
      const lines = block.split("\n").map((l) => l.trim()).filter(Boolean);
      const bullets = lines.filter((l) => /^[-•]\s+/.test(l));
      if (bullets.length === lines.length && bullets.length) {
        const ul = document.createElement("ul");
        bullets.forEach((b) => {
          const li = document.createElement("li");
          li.textContent = b.replace(/^[-•]\s+/, "");
          ul.appendChild(li);
        });
        container.appendChild(ul);
      } else {
        const p = document.createElement("p");
        p.textContent = lines.join(" ");
        container.appendChild(p);
      }
    });
    return container;
  }

  function citationNode(citation, index) {
    const item = document.createElement("div");
    item.className = "cite-item";
    const url = citation.url ? String(citation.url) : "";
    item.innerHTML = `
      <span class="cite-num">${index + 1}</span>
      <div class="cite-main">
        <div class="cite-name">${esc(citation.source_name)}</div>
        <div class="cite-meta">
          ${citation.section ? `${esc(citation.section)}<span class="sep">|</span>` : ""}
          ${esc(citation.source_type)}
        </div>
        ${url ? `<a class="cite-link" href="${esc(url)}" target="_blank" rel="noopener noreferrer">
          ${esc(url.replace(/^https?:\/\//, "").slice(0, 60))}${url.length > 67 ? "…" : ""}
          <svg class="icon"><use href="#i-ext"/></svg></a>` : ""}
      </div>`;
    return item;
  }

  function setMeta(response, seconds, kind) {
    if (!response) {
      els.metaEmpty().classList.remove("hidden");
      els.metaList().classList.add("hidden");
      return;
    }
    const langName = state.language === "hi" ? "हिन्दी" : "English";
    const statusKey = kind === "error" ? "statusError"
      : response.abstention ? "statusAbstained" : "statusAnswered";
    const statusClass = kind === "error" ? "status-error"
      : response.abstention ? "status-abstained" : "status-ok";
    const timeKey = response.abstention ? "abstainedIn" : "answeredIn";
    const rows = [
      [I18N.t("rowStatus"), `<span class="${statusClass}">${esc(I18N.t(statusKey))}</span>`, true],
      [I18N.t("rowConfidence"),
        `<span class="conf-badge conf-${esc(response.confidence)}">${esc(response.confidence)}</span> `
        + `<span class="conf-score">${Number(response.confidence_score).toFixed(2)}</span>`, true],
      [I18N.t("rowJurisdiction"), esc(state.jurisdiction), true],
      [I18N.t("rowLanguage"), esc(langName), true],
      [I18N.t("rowFormulation"), esc(state.formulationClass || I18N.t("autoDetect")), true],
      [I18N.t("rowSources"), String((response.citations || []).length), true],
      [I18N.t("rowTime"), esc(I18N.t(timeKey).replace("{s}", seconds.toFixed(2))), true],
    ];
    els.metaList().innerHTML = rows
      .map(([label, value]) => `<div class="meta-row"><dt>${label}</dt><dd>${value}</dd></div>`)
      .join("");
    els.metaEmpty().classList.add("hidden");
    els.metaList().classList.remove("hidden");
  }

  function setSources(citations) {
    if (!citations || !citations.length) {
      els.sourcesList().innerHTML = "";
      els.sourcesEmpty().classList.remove("hidden");
      return;
    }
    els.sourcesEmpty().classList.add("hidden");
    els.sourcesList().innerHTML = "";
    citations.forEach((citation, index) => {
      els.sourcesList().appendChild(citationNode(citation, index));
    });
  }

  function renderAbstention(shell, response) {
    shell.body.innerHTML = "";
    const banner = document.createElement("div");
    banner.className = "abstain-banner";
    banner.innerHTML = `
      <svg class="icon"><use href="#i-shieldq"/></svg>
      <div>
        <div class="abstain-title">${esc(I18N.t("abstainTitle"))}</div>
        <div class="abstain-reason">${esc(response.abstention_reason || "")}</div>
      </div>`;
    shell.body.appendChild(banner);
    if (response.answer && response.answer.trim()) {
      shell.body.appendChild(answerParagraphs(response.answer));
    }
    const classificationCue = /classif/i.test(response.abstention_reason || "");
    if (classificationCue) {
      const row = document.createElement("p");
      row.style.marginTop = "10px";
      const button = document.createElement("button");
      button.type = "button";
      button.className = "btn-ghost btn-small";
      button.textContent = I18N.t("openClassifier");
      button.addEventListener("click", () => switchView("classifier"));
      row.appendChild(button);
      shell.body.appendChild(row);
    }
    addFoot(shell, response);
  }

  function renderAnswer(shell, response) {
    shell.body.innerHTML = "";
    shell.body.appendChild(answerParagraphs(response.answer));

    const section = document.createElement("div");
    section.className = "answer-section";
    section.innerHTML = `
      <div class="answer-section-label"><svg class="icon"><use href="#i-gauge"/></svg><span>${esc(I18N.t("confidenceLabel"))}</span></div>
      <div class="conf-row">
        <span class="conf-badge conf-${esc(response.confidence)}">${esc(response.confidence)}</span>
        <span class="conf-score">${Number(response.confidence_score).toFixed(2)}</span>
        <span class="conf-bar"><span class="conf-bar-fill${Number(response.confidence_score) < 0.5 ? " m-low" : ""}"
          style="width:${Math.round(Number(response.confidence_score) * 100)}%"></span></span>
      </div>`;
    shell.body.appendChild(section);

    if (response.citations && response.citations.length) {
      const citeSection = document.createElement("div");
      citeSection.className = "answer-section";
      const list = document.createElement("div");
      list.className = "cite-list";
      response.citations.forEach((citation, index) => {
        list.appendChild(citationNode(citation, index));
      });
      citeSection.innerHTML = `
        <div class="answer-section-label"><svg class="icon"><use href="#i-file"/></svg><span>${esc(I18N.t("sourcesLabel"))} · ${response.citations.length}</span></div>`;
      citeSection.appendChild(list);
      shell.body.appendChild(citeSection);
    }
    addFoot(shell, response);
  }

  function addFoot(shell, response) {
    const foot = document.createElement("div");
    foot.className = "answer-foot";
    foot.textContent = response.disclaimer || "";
    shell.card.appendChild(foot);
  }

  function renderErrorShell(err) {
    const shell = addAssistantShell();
    const message = err.kind === "network" ? I18N.t("errNetwork")
      : err.status === 400 ? I18N.t("errValidation")
      : err.status === 502 ? I18N.t("errProcessing")
      : err.status === 503 ? I18N.t("errUnavailable")
      : I18N.t("errGeneric");
    shell.body.innerHTML = `
      <div class="error-banner"><svg class="icon"><use href="#i-alert"/></svg><span>${esc(message)}</span></div>`;
    const foot = document.createElement("div");
    foot.className = "answer-foot";
    foot.textContent = I18N.t("disclaimerBody");
    shell.card.appendChild(foot);
    setMeta({ abstention: false, confidence: "LOW", confidence_score: 0, citations: [] }, 0, "error");
  }

  /* ── request flow ───────────────────────────────────────────────── */

  async function sendQuery(text) {
    if (state.busy) return;
    const query = (text || "").trim();
    if (!query) return;

    state.busy = true;
    els.sendBtn().disabled = true;
    els.input().value = "";
    addUserMessage(query);
    const shell = addAssistantShell();
    const started = performance.now();

    try {
      const response = await API.query({
        id: `web-${Date.now()}`,
        query,
        language: state.language,
        jurisdiction: state.jurisdiction,
        formulation_class: state.formulationClass,
        history: state.history,
      });
      const seconds = (performance.now() - started) / 1000;
      shell.body.innerHTML = "";
      if (response.abstention) {
        renderAbstention(shell, response);
      } else {
        renderAnswer(shell, response);
      }
      setMeta(response, seconds);
      setSources(response.citations);
      state.history.push({ role: "user", content: query });
      state.history.push({ role: "assistant", content: String(response.answer || "") });
      if (state.history.length > 20) state.history = state.history.slice(-20);
    } catch (err) {
      renderErrorShell(err);
    } finally {
      state.busy = false;
      els.sendBtn().disabled = false;
      els.input().focus();
    }
  }

  /* ── demo scenario cards ────────────────────────────────────────── */

  function initDemoCards() {
    document.querySelectorAll(".demo-card").forEach((card) => {
      card.addEventListener("click", () => {
        const scenario = card.dataset.scenario;
        if (scenario === "classification") {
          switchView("classifier");
          Classifier.prefill(CLASSIFIER_EXAMPLE);
          Classifier.classify();
          return;
        }
        const spec = SCENARIOS[scenario];
        if (!spec) return;
        switchView("chat");
        if (spec.jurisdiction !== state.jurisdiction) {
          state.jurisdiction = spec.jurisdiction;
          document.querySelectorAll("#jurisdictionToggle .seg").forEach((s) =>
            s.classList.toggle("active", s.dataset.value === spec.jurisdiction));
          updateJurisdictionNote();
        }
        sendQuery(spec.query);
      });
    });
  }

  /* ── boot ───────────────────────────────────────────────────────── */

  function initFormulationOptions() {
    // Contract-legal FormulationClass values (Plan.md §7) — machine values,
    // mirrored from the backend contract; classifier questions come from the
    // backend separately.
    const values = ["Classical", "Proprietary", "Phytopharmaceutical",
      "Ayurveda-Aahar", "Cosmetic", "New Drug", "Uncertain"];
    const select = el("formulationSelect");
    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    });
  }

  function init() {
    initShell();
    initFormulationOptions();
    initDemoCards();
    Classifier.init();
    refreshHealth();
    window.setInterval(refreshHealth, 30000);

    els.composer().addEventListener("submit", (event) => {
      event.preventDefault();
      sendQuery(els.input().value);
    });
    els.input().addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendQuery(els.input().value);
      }
    });
    // auto-grow textarea
    els.input().addEventListener("input", () => {
      const input = els.input();
      input.style.height = "auto";
      input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
    });
  }

  document.addEventListener("DOMContentLoaded", init);
  return { sendQuery, switchView };
})();
