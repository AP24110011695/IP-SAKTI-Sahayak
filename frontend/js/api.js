/* api.js — thin fetch wrappers around the real integrated backend.
   Same-origin (the backend serves this frontend), no mocking layers. */
"use strict";

const API = (() => {
  async function request(path, options) {
    let response;
    try {
      response = await fetch(path, options);
    } catch (networkError) {
      const err = new Error("network");
      err.kind = "network";
      throw err;
    }
    let body = null;
    try { body = await response.json(); } catch (parseError) { /* non-JSON */ }
    if (!response.ok) {
      const err = new Error((body && body.error) || `HTTP ${response.status}`);
      err.kind = "api";
      err.status = response.status;
      err.code = body && body.error;
      err.message = body && body.message;
      throw err;
    }
    return body;
  }

  return {
    health: () => request("/api/health", { method: "GET" }),

    query: (payload) => request("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

    classify: (payload) => request("/api/classify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

    classifyQuestions: () => request("/api/classify/questions", { method: "GET" }),
  };
})();
