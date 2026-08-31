/* US-3 barcode scanner: BarcodeDetector API + camera, with a manual barcode
   fallback so the dashboard still works when the camera is unavailable. */
(function () {
  "use strict";

  var video = document.getElementById("barcode-video");
  var scanBtn = document.getElementById("scan-btn");
  var manualInput = document.getElementById("barcode-manual");
  var lookupBtn = document.getElementById("barcode-lookup-btn");
  var resultBox = document.getElementById("barcode-result");
  var stream = null;
  var detector = null;
  var timer = null;

  function stopScanner() {
    if (timer) { clearInterval(timer); timer = null; }
    if (stream) { stream.getTracks().forEach(function (t) { t.stop(); }); stream = null; }
    video.srcObject = null;
    video.classList.add("hidden");
    scanBtn.textContent = "Scansiona codice a barre";
  }

  function lookup(code) {
    code = String(code || "").trim();
    if (!code) return;
    resultBox.innerHTML = '<p class="text-sm text-slate-400 px-4 py-3">Ricerca in corso…</p>';
    fetch("/api/foods/barcode/" + encodeURIComponent(code), {
      headers: { "HX-Request": "true" },
    })
      .then(function (resp) { return resp.text(); })
      .then(function (html) { resultBox.innerHTML = html; })
      .catch(function () {
        resultBox.innerHTML =
          '<p class="text-sm text-amber-300 px-4 py-3">Errore di rete, riprova.</p>';
      });
  }

  function onDetected(code) {
    if (!code) return;
    manualInput.value = code;
    stopScanner();
    lookup(code);
  }

  function startScanner() {
    if (!("BarcodeDetector" in window) || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      resultBox.innerHTML =
        '<p class="text-sm text-amber-300 px-4 py-3">Scanner fotocamera non disponibile: inserisci il codice a barre manualmente.</p>';
      manualInput.focus();
      return;
    }
    var formats;
    try {
      formats = ["ean_13", "ean_8", "upc_a", "upc_e", "code_128"];
      detector = new window.BarcodeDetector({ formats: formats });
    } catch (err) {
      detector = new window.BarcodeDetector();
    }
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then(function (s) {
        stream = s;
        video.srcObject = s;
        video.classList.remove("hidden");
        scanBtn.textContent = "Annulla scansione";
        return video.play();
      })
      .then(function () {
        timer = setInterval(function () {
          if (!detector) return;
          detector.detect(video).then(function (codes) {
            if (codes && codes.length) onDetected(codes[0].rawValue);
          }).catch(function () {});
        }, 300);
      })
      .catch(function () {
        resultBox.innerHTML =
          '<p class="text-sm text-amber-300 px-4 py-3">Fotocamera non disponibile: inserisci il codice a barre manualmente.</p>';
        manualInput.focus();
      });
  }

  if (scanBtn) {
    scanBtn.addEventListener("click", function () {
      if (stream) { stopScanner(); } else { startScanner(); }
    });
  }
  if (lookupBtn) {
    lookupBtn.addEventListener("click", function () { lookup(manualInput.value); });
  }
  if (manualInput) {
    manualInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter") {
        event.preventDefault();
        lookup(manualInput.value);
      }
    });
  }

  // Confirm button inside the lookup fragment reuses the quick-log form.
  document.addEventListener("click", function (event) {
    var btn = event.target.closest("#barcode-result #barcode-confirm");
    if (!btn) return;
    var map = {
      "food-id": btn.dataset.foodId,
      "food-name": btn.dataset.name,
      "food-brand": btn.dataset.brand,
      "food-kcal": btn.dataset.kcal,
      "food-protein": btn.dataset.protein,
      "food-carbs": btn.dataset.carbs,
      "food-fat": btn.dataset.fat,
    };
    for (var id in map) {
      var el = document.getElementById(id);
      if (el) el.value = map[id];
    }
    var selected = document.getElementById("selected-food");
    if (selected) {
      selected.textContent =
        "Selezionato: " + btn.dataset.name + (btn.dataset.brand ? " (" + btn.dataset.brand + ")" : "");
    }
    resultBox.innerHTML = "";
    var grams = document.getElementById("grams");
    if (grams) grams.focus();
  });
})();
