/**
 * Speak text using the browser Web Speech API.
 * lang: BCP 47 tag, e.g. "fr", "de", "hr". Falls back to "en" if unsupported.
 */
function speak(text, lang) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = lang || "en";
  window.speechSynthesis.speak(utt);
}
