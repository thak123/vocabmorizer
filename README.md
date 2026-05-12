# Vocabmorizer

A web application for learning and practising vocabulary and phrases in a second language using spaced repetition and context-based learning.

## Features

- **Add Vocabulary**: Input vocabulary entries with multiple fields including synonyms, antonyms, meanings, translations, and morphological usage examples
- **Lightweight Storage**: All data stored locally in a lightweight dataset (JSON/SQLite) — no cloud dependency
- **Smart Practice**: Review vocabulary based on multiple criteria: lecture, date range, difficulty, or random selection
- **Audio Support**: Text-to-speech for individual words or full example sentences to improve pronunciation
- **Progress Tracking**: Monitor your learning progress with stats on reviewed items and retention

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/thak123/vocabmorizer.git
cd vocabmorizer

# Install dependencies
uv sync

# Run the application
python -m vocabmorizer
```

The application will start at `http://localhost:5000`


http://vocabmorizer.duckdns.org:8080`/

### Basic Usage

1. **Add Vocabulary**: Click "Add New Word" and fill in the fields:
   - Word, Synonyms, Antonyms
   - Meaning, English translation
   - Usage examples and morphological notes
   - Associated lecture and date

2. **Practice**: Go to the Practice page and select your criteria:
   - Filter by lecture
   - Filter by date range
   - Choose difficulty level
   - Or review randomly

3. **Listen**: Click the speaker icon to hear pronunciation of any word or example sentence

## Project Structure

- `app/` — Flask web application
- `data/` — Local dataset storage
- `static/` — Frontend assets (CSS, JavaScript)
- `templates/` — HTML templates

## Development

```bash
# Run tests
pytest

# Format code
ruff format .

# Lint
ruff check .
```

## Data Model

Each vocabulary entry contains:
- Lecture (course/section identifier)
- Date (when added)
- Word (the vocabulary item)
- Synonym, Antonym, Meaning, Translation
- Metadata/usage (morphological examples)

See [SPECIFICATION.md](SPECIFICATION.md) for detailed schema.

## License

MIT License — see LICENSE file
