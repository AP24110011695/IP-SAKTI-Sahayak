/* classifier.js — Formulation Classifier view.
   Questions come from the backend's /api/classify/questions (Member 2's own
   get_questions()); classification comes from POST /api/classify. The UI
   contains no classification logic of its own. */
"use strict";

const Classifier = (() => {
  let questions = [];
  let selectedAnswers = {};
  let lastResult = null;

  const els = {
    view: () => document.getElementById("view-classifier"),
    questions: () => document.getElementById("classifierQuestions"),
    form: () => document.getElementById("classifierForm"),
    result: () => document.getElementById("classifierResult"),
    jurisdiction: () => document.getElementById("clsJurisdiction"),
    reset: () => document.getElementById("clsReset"),
  };

  function esc(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  /* ── question rendering ─────────────────────────────────────────── */

  async function loadQuestions() {
    els.questions().innerHTML = `<p class="muted">${esc(I18N.t("loadingQuestions"))}</p>`;
    try {
      const data = await API.classifyQuestions();
      questions = data.questions;
      renderQuestions();
    } catch (err) {
      els.questions().innerHTML =
        `<div class="error-banner"><svg class="icon"><use href="#i-alert"/></svg>` +
        `<span>${esc(I18N.t("errNetwork"))}</span></div>`;
    }
  }

  function renderQuestions() {
    const lang = I18N.lang;
    els.questions().innerHTML = questions.map((q) => {
      const optionKeys = Object.keys(q.options);
      const rows = optionKeys.map((key) => {
        const checked = selectedAnswers[q.id] === key ? " selected" : "";
        const labelMain = lang === "hi" ? q.options_hi[key] : q.options[key];
        const labelAlt = lang === "hi" ? q.options[key] : q.options_hi[key];
        return `
          <label class="cls-option${checked}">
            <input type="radio" name="${esc(q.id)}" value="${esc(key)}"
              ${selectedAnswers[q.id] === key ? "checked" : ""}>
            <span>
              <span class="opt-label">${esc(labelMain)}</span>
              <span class="opt-hi">${esc(labelAlt)}</span>
            </span>
          </label>`;
      }).join("");
      const questionMain = lang === "hi" ? q.text_hi : q.text;
      const questionAlt = lang === "hi" ? q.text : q.text_hi;
      return `
        <fieldset class="cls-question" data-question="${esc(q.id)}">
          <legend class="visually-hidden">${esc(q.id)}</legend>
          <p class="cls-q">${esc(questionMain)}</p>
          <p class="cls-q-hi">${esc(questionAlt)}</p>
          <div class="cls-options">${rows}</div>
        </fieldset>`;
    }).join("");

    els.questions().querySelectorAll("input[type=radio]").forEach((input) => {
      input.addEventListener("change", () => {
        selectedAnswers[input.name] = input.value;
        const fieldset = input.closest(".cls-option");
        fieldset.parentElement.querySelectorAll(".cls-option").forEach((o) => o.classList.remove("selected"));
        fieldset.classList.add("selected");
      });
    });
  }

  /* ── classification ─────────────────────────────────────────────── */

  async function classify() {
    const payload = {
      answers: { ...selectedAnswers },
      jurisdiction: els.jurisdiction().value || "India",
      language: I18N.lang,
    };
    els.result().classList.remove("hidden");
    els.result().innerHTML = `<p class="muted"><span class="typing"><i></i><i></i><i></i></span></p>`;
    const started = performance.now();
    try {
      const result = await API.classify(payload);
      lastResult = result;
      renderResult(result, (performance.now() - started) / 1000);
    } catch (err) {
      renderError(err);
    }
  }

  function confBadge(result) {
    const score = result.confidence_score != null ? Number(result.confidence_score) : null;
    return `
      <div class="conf-row">
        <span class="conf-badge conf-${esc(result.confidence)}">${esc(result.confidence)}</span>
        ${score != null ? `<span class="conf-score">${score.toFixed(2)}</span>` : ""}
        ${score != null ? `<span class="conf-bar"><span class="conf-bar-fill${score < 0.5 ? " m-low" : ""}" style="width:${Math.round(score * 100)}%"></span></span>` : ""}
      </div>`;
  }

  function renderResult(result, seconds) {
    const lang = I18N.lang;
    const uncertain = result.formulation_class === "Uncertain";
    const label = lang === "hi"
      ? (result.category_labels && result.category_labels.hi) || result.formulation_class
      : (result.category_labels && result.category_labels.en) || result.formulation_class;

    const regimes = (result.relevant_regimes || []).map((r) => `<li>${esc(r)}</li>`).join("");
    const regimesBlock = regimes
      ? `<h4 class="result-sub">${esc(I18N.t("relevantRegimes"))}</h4><ul class="cls-regimes">${regimes}</ul>`
      : "";

    const tkdlBlock = result.tkdl_pointer
      ? `<div class="cls-tkdl"><strong>${esc(I18N.t("tkdlHeading"))}:</strong> ${esc(result.tkdl_pointer)}</div>`
      : "";

    const clarifyBlock = result.needs_clarification && result.clarification_prompt
      ? `<div class="cls-clarify"><strong>${esc(I18N.t("clarificationNeeded"))}:</strong> ${esc(result.clarification_prompt)}</div>`
      : "";

    let suggestedBlock = "";
    if (Array.isArray(result.suggested_questions) && result.suggested_questions.length) {
      const items = result.suggested_questions.map((sq) => {
        const text = lang === "hi" ? (sq.hi || sq.en) : (sq.en || sq.hi);
        return `<li>${esc(text)}</li>`;
      }).join("");
      suggestedBlock = `<h4 class="result-sub">${esc(I18N.t("suggestedQuestions"))}</h4><ul class="cls-suggested">${items}</ul>`;
    }

    let reasoningBlock = "";
    if (Array.isArray(result.reasoning) && result.reasoning.length) {
      const items = result.reasoning.map((r) => `<li>${esc(r)}</li>`).join("");
      reasoningBlock = `<details class="cls-reasoning"><summary>${esc(I18N.t("reasoningTrace"))}</summary><ul>${items}</ul></details>`;
    }

    els.result().innerHTML = `
      <div class="cls-result-head">
        <span class="cls-class-badge${uncertain ? " uncertain" : ""}">${esc(label)}</span>
      </div>
      ${confBadge(result)}
      <p class="cls-desc">${esc(result.description)}</p>
      ${clarifyBlock}
      ${regimesBlock}
      ${tkdlBlock}
      ${suggestedBlock}
      ${reasoningBlock}
      <p class="answer-foot">${esc(I18N.t("disclaimerTitle"))}: ${esc(I18N.t("disclaimerBody"))}</p>`;

    highlightBlocking(result);
  }

  function renderError(err) {
    const message = err.kind === "network" ? I18N.t("errNetwork")
      : err.status === 400 ? I18N.t("errValidation")
      : err.status === 502 ? I18N.t("errProcessing")
      : err.status === 503 ? I18N.t("errUnavailable")
      : I18N.t("errGeneric");
    els.result().innerHTML = `
      <div class="error-banner"><svg class="icon"><use href="#i-alert"/></svg><span>${esc(message)}</span></div>`;
  }

  function highlightBlocking(result) {
    els.questions().querySelectorAll(".cls-option").forEach((o) => o.classList.remove("needs-attention"));
    const ids = result.clarification_question_ids || [];
    ids.forEach((id) => {
      const fieldset = els.questions().querySelector(`fieldset[data-question="${CSS.escape(id)}"]`);
      if (fieldset) {
        fieldset.querySelectorAll(".cls-option").forEach((o) => o.classList.add("needs-attention"));
      }
    });
  }

  function reset() {
    selectedAnswers = {};
    lastResult = null;
    els.result().classList.add("hidden");
    els.result().innerHTML = "";
    renderQuestions();
  }

  function prefill(answers) {
    selectedAnswers = { ...answers };
    renderQuestions();
  }

  function show() {
    els.view().classList.remove("hidden");
    if (!questions.length) loadQuestions();
  }

  function init() {
    els.form().addEventListener("submit", (event) => {
      event.preventDefault();
      classify();
    });
    els.reset().addEventListener("click", reset);
    document.addEventListener("i18n:changed", () => {
      if (questions.length) {
        renderQuestions();
        if (lastResult) renderResult(lastResult, 0);
      }
    });
  }

  return { init, show, hide: () => els.view().classList.add("hidden"), prefill, classify };
})();
