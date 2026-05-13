/**
 * TTS helpers + VocabPlayer for sequential word playback.
 */

// Speak a single utterance. voiceURI is optional.
function speak(text, lang, voiceURI) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utt = new SpeechSynthesisUtterance(text);
  utt.lang = lang || "en";
  if (voiceURI) {
    const v = speechSynthesis.getVoices().find(v => v.voiceURI === voiceURI);
    if (v) utt.voice = v;
  }
  window.speechSynthesis.speak(utt);
}

// Return voices available for a BCP-47 language prefix (e.g. "hr", "es").
function getVoicesForLang(lang) {
  const all = window.speechSynthesis ? speechSynthesis.getVoices() : [];
  if (!lang) return all;
  const prefix = lang.split("-")[0].toLowerCase();
  const matched = all.filter(v => v.lang.toLowerCase().startsWith(prefix));
  return matched.length ? matched : all; // fall back to all if none match
}

// ---------------------------------------------------------------------------
// VocabPlayer — sequential playback of a word list
// ---------------------------------------------------------------------------
class VocabPlayer {
  constructor({ onStart, onWord, onEnd, onStop } = {}) {
    this._queue = [];     // [{word, translation, lang}]
    this._index = 0;
    this._paused = false;
    this._stopped = true;
    this._rate = 1.0;
    this._voiceURI = null;
    this.onStart = onStart || (() => {});
    this.onWord  = onWord  || (() => {});
    this.onEnd   = onEnd   || (() => {});
    this.onStop  = onStop  || (() => {});
  }

  load(items) { this._queue = items; this._index = 0; }
  setRate(r)  { this._rate = r; }
  setVoice(uri) { this._voiceURI = uri; }

  play() {
    if (!window.speechSynthesis) return;
    this._stopped = false;
    this._paused = false;
    if (this._index >= this._queue.length) this._index = 0;
    this.onStart();
    this._speak();
  }

  pause() {
    if (!window.speechSynthesis || this._stopped) return;
    this._paused = true;
    speechSynthesis.pause();
  }

  resume() {
    if (!window.speechSynthesis || this._stopped) return;
    this._paused = false;
    speechSynthesis.resume();
  }

  stop() {
    this._stopped = true;
    this._paused = false;
    if (window.speechSynthesis) speechSynthesis.cancel();
    this.onStop();
  }

  next() {
    speechSynthesis.cancel();
    this._index = Math.min(this._index + 1, this._queue.length);
    if (!this._stopped && !this._paused) this._speak();
  }

  prev() {
    speechSynthesis.cancel();
    this._index = Math.max(this._index - 1, 0);
    if (!this._stopped && !this._paused) this._speak();
  }

  _speak() {
    if (this._stopped) return;
    if (this._index >= this._queue.length) { this.onEnd(); return; }

    const item = this._queue[this._index];
    this.onWord(this._index, item);

    const utt = new SpeechSynthesisUtterance(item.word);
    utt.lang = item.lang || "en";
    utt.rate = this._rate;
    if (this._voiceURI) {
      const v = speechSynthesis.getVoices().find(v => v.voiceURI === this._voiceURI);
      if (v) utt.voice = v;
    }

    utt.onend = () => {
      if (this._stopped) return;
      // Pause 600 ms then speak translation
      setTimeout(() => {
        if (this._stopped) return;
        const utt2 = new SpeechSynthesisUtterance(item.translation);
        utt2.lang = "en";
        utt2.rate = this._rate;
        utt2.onend = () => {
          if (this._stopped) return;
          this._index++;
          setTimeout(() => this._speak(), 800); // gap between words
        };
        speechSynthesis.speak(utt2);
      }, 600);
    };

    speechSynthesis.speak(utt);
  }
}

// Singleton player instance shared across the page
window._vocabPlayer = window._vocabPlayer || new VocabPlayer();
