(function () {
  const root = document.getElementById("practice-root");
  if (!root) return;

  const entryId = root.dataset.entryId;
  const recordUrl = root.dataset.recordUrl;
  const lang = root.dataset.lang;

  const revealBtn = document.getElementById("reveal-btn");
  const answerSection = document.getElementById("answer-section");
  const resultBtns = document.getElementById("result-btns");

  revealBtn.addEventListener("click", function () {
    answerSection.classList.remove("hidden");
    resultBtns.classList.remove("hidden");
    revealBtn.classList.add("hidden");
    // Auto-speak the word on reveal
    if (typeof speak === "function") speak(answerSection.querySelector(".text-3xl").textContent.trim(), lang);
  });

  resultBtns.querySelectorAll(".result-btn").forEach(function (btn) {
    btn.addEventListener("click", async function () {
      const result = btn.dataset.result;

      // Disable all buttons to prevent double-submit
      resultBtns.querySelectorAll(".result-btn").forEach(b => b.disabled = true);

      try {
        const resp = await fetch(recordUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ entry_id: entryId, result }),
        });
        const data = await resp.json();
        if (data.next) {
          window.location.href = data.next;
        }
      } catch {
        // Re-enable on network error
        resultBtns.querySelectorAll(".result-btn").forEach(b => b.disabled = false);
      }
    });
  });
})();
