# SPECIFICATION.md — Vocabmorizer

## Project Overview

Vocabmorizer is a web-based vocabulary learning platform designed for second-language learners. Users input vocabulary entries with contextual information (synonyms, antonyms, translations, usage examples) and then practice with those entries using flexible filtering and spaced repetition principles.

## Core Features

### 1. Data Entry Page

Users can add new vocabulary entries through a form with the following fields:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Lecture | String | Yes | Course/section identifier (e.g., "French 101", "Chapter 3") |
| Date | Date | Yes | When the word was added/learned |
| Word | String | Yes | The vocabulary item in target language |
| Synonym | String[] | No | One or more synonyms |
| Antonym | String[] | No | One or more antonyms |
| Meaning | Text | Yes | Definition in target language |
| Translation-en | String | Yes | English translation |
| Metadata/Usage | Text | No | Morphological notes, example sentences, usage patterns |

### 2. Practice/Review Page

Users practice vocabulary with multiple filtering and selection options:

- **Filter by Lecture**: Choose specific lectures/sections
- **Filter by Date**: Select a date range of entries to review
- **Filter by Frequency**: Review recently learned vs. older entries
- **Random Mode**: Select entries randomly from entire dataset
- **Difficulty Level**: Option to focus on words marked as hard/medium/easy

Display shows:
- The target language word
- One of: meaning, synonym, antonym, or translation (randomly selected as prompt)
- User must identify or recall the word
- Option to reveal answer
- User marks as: correct/incorrect/need-review

### 3. Audio/Text-to-Speech

All vocabulary entries support audio playback:
- Click speaker icon on any word to hear pronunciation
- Click speaker icon on usage examples to hear full sentence
- Uses browser's Web Speech API or external TTS service

### 4. Data Persistence

All data stored locally in lightweight format:
- **Option A**: JSON files in `data/` directory (simplest, human-readable)
- **Option B**: SQLite database (better for scalability)
- No cloud upload — all data stays local to user's machine

## Data Schema

### Vocabulary Entry

```json
{
  "id": "uuid",
  "lecture": "French 101",
  "date_added": "2026-05-06",
  "word": "serendipité",
  "synonyms": ["chance heureuse"],
  "antonyms": [],
  "meaning": "Découverte heureuse par hasard",
  "translation_en": "Serendipity",
  "metadata": {
    "morphology": "noun (feminine)",
    "usage_examples": [
      "C'était pure serendipité de les rencontrer.",
      "La vie est pleine de serendipité."
    ]
  },
  "review_stats": {
    "times_reviewed": 5,
    "correct_count": 3,
    "difficulty": "medium",
    "last_reviewed": "2026-05-05"
  }
}
```

## User Workflows

### Workflow 1: Add New Vocabulary

1. User clicks "Add New Word"
2. Form opens with all fields
3. User fills in required fields (Word, Meaning, Translation-en, Lecture, Date)
4. User optionally adds Synonyms, Antonyms, Usage examples
5. User clicks "Save"
6. Entry is added to dataset and confirmation shown

### Workflow 2: Practice Vocabulary

1. User navigates to "Practice" page
2. Selects filtering criteria (lecture, date range, etc.)
3. System loads matching entries
4. For each word:
   - Display is shown (e.g., English translation)
   - User attempts to recall the word
   - User clicks "Show Answer" or submits guess
   - User marks as correct/incorrect/need-review
5. After all entries reviewed, show summary stats

### Workflow 3: Hear Word Pronunciation

1. User is on Add or Practice page
2. User clicks speaker icon next to word
3. Text-to-speech plays pronunciation
4. If example sentence, speaker icon triggers playback of full sentence

## Technical Requirements

### Frontend
- Web framework: Flask or FastAPI
- Frontend: HTML5 + JavaScript (vanilla or Vue.js)
- Styling: CSS or Tailwind
- Audio API: Web Speech API or integration with external TTS service

### Backend
- Language: Python
- Data storage: JSON files or SQLite
- No authentication/login required (single-user local app)

### Browser Compatibility
- Modern browsers with Web Speech API support (Chrome, Firefox, Safari, Edge)
- No specific mobile responsiveness required (desktop-first)

## Future Enhancements

- Spaced repetition algorithm (SM-2 or similar)
- Export/import vocabulary lists (CSV, Anki)
- Difficulty scoring based on correct/incorrect history
- Statistics dashboard (words learned, accuracy, time spent)
- Multiple language pairs (not just EN ↔ target)
- Image/example associations
- Cloud backup option
- Collaborative vocabulary lists

## Non-Goals

- Multimedia pronunciation library (using system TTS only)
- Social features or community sharing
- Mobile app (web-based only)
- Real-time collaboration
- Advanced NLP processing
