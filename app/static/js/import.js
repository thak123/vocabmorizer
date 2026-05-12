(function () {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const dropLabel = document.getElementById("drop-label");
  const form = document.getElementById("import-form");
  const progressBar = document.getElementById("progress-bar");
  const submitBtn = document.getElementById("submit-btn");

  if (!dropZone) return;

  function highlight() { dropZone.classList.add("border-indigo-500", "bg-indigo-50"); }
  function unhighlight() { dropZone.classList.remove("border-indigo-500", "bg-indigo-50"); }

  dropZone.addEventListener("dragover", (e) => { e.preventDefault(); highlight(); });
  dropZone.addEventListener("dragleave", unhighlight);
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    unhighlight();
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      fileInput.files = dt.files;
      dropLabel.textContent = file.name;
    }
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) dropLabel.textContent = fileInput.files[0].name;
  });

  form.addEventListener("submit", () => {
    if (!fileInput.files[0]) return;
    submitBtn.disabled = true;
    progressBar.classList.remove("hidden");
  });
})();
