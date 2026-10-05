/* =============================================================================
 * VARIATION {{VN}} - {{NOM_DU_TEST}}
 * Hypothese : {{HYPOTHESE}}
 * Cibles    : {{LISTE_SELECTEURS}}
 * Changelog : {{CHANGELOG}}
 * ============================================================================= */
(function () {
  "use strict";

  var VARIATION = "abt-v1"; // classe racine : scope CSS + idempotence + rollback
  var AFL_ID    = "abt-v1-afl"; // id du style anti-flicker

  /* Anti-flicker integre : masque la zone modifiee avant tout paint, le temps
     que apply() s'execute. Timeout de securite 3s : ne JAMAIS laisser la page
     masquee si le JS echoue. Regle CSS complete dans variation.css (.abt-v1-hide),
     scopee a la zone reellement modifiee (pas body entier). */
  var afl = document.createElement("style");
  afl.id = AFL_ID;
  document.documentElement.classList.add("abt-v1-hide");
  (document.head || document.documentElement).appendChild(afl);
  var aflTimer = setTimeout(removeAntiFlicker, 3000);

  function removeAntiFlicker() {
    clearTimeout(aflTimer);
    document.documentElement.classList.remove("abt-v1-hide");
    if (afl.parentNode) afl.parentNode.removeChild(afl);
  }

  // Idempotence : ne pas reappliquer si deja fait (navigation SPA)
  if (document.documentElement.classList.contains(VARIATION)) {
    removeAntiFlicker();
    return;
  }
  document.documentElement.classList.add(VARIATION);

  // Utilitaire : attendre l'apparition d'un element (DOM dynamique)
  function waitForElement(selector, opts) {
    opts = opts || {};
    var timeout = opts.timeout || 5000;
    return new Promise(function (resolve, reject) {
      var found = document.querySelector(selector);
      if (found) return resolve(found);
      var obs = new MutationObserver(function () {
        var el = document.querySelector(selector);
        if (el) { obs.disconnect(); resolve(el); }
      });
      obs.observe(document.documentElement, { childList: true, subtree: true });
      setTimeout(function () { obs.disconnect(); reject(new Error("timeout: " + selector)); }, timeout);
    });
  }

  // Utilitaire : fallback par texte si pas de selecteur stable
  function findByText(selector, text) {
    var t = text.trim().toLowerCase();
    return Array.prototype.slice.call(document.querySelectorAll(selector))
      .find(function (el) { return el.textContent.trim().toLowerCase() === t; });
  }

  // Utilitaire : modifier un texte en sauvegardant l'original (rollback)
  function setText(el, value) {
    if (!el) return;
    if (el.dataset.abtOriginal === undefined) el.dataset.abtOriginal = el.textContent;
    el.textContent = value;
    el.setAttribute("data-abt", VARIATION);
  }

  // Utilitaire : inserer un noeud (marque pour le cleanup)
  function injectAfter(refEl, node) {
    if (!refEl) return;
    node.setAttribute("data-abt", VARIATION);
    refEl.insertAdjacentElement("afterend", node);
  }

  // Application des changements
  function apply() {
    /* EXEMPLE - a adapter au brief. Appeler removeAntiFlicker() a la fin de
       CHAQUE chemin (succes, catch, cible introuvable) pour ne jamais laisser
       la page masquee au-dela du timeout de securite :
    waitForElement("h1.product-title").then(function (title) {
      setText(title, "Nouveau titre");
      removeAntiFlicker();
    }).catch(function (e) {
      console.warn("[abt]", e.message);
      removeAntiFlicker();
    });
    */
    removeAntiFlicker(); // a deplacer dans le .then()/.catch() reel ci-dessus
  }

  if (document.readyState !== "loading") apply();
  else document.addEventListener("DOMContentLoaded", apply);
})();
