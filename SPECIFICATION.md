# SPECIFICATION.md — Vocabmorizer

## Project Overview

Vocabmorizer is a web-based vocabulary learning platform designed for second-language learners. Users input vocabulary entries with contextual information (synonyms, antonyms, translations, usage examples) and then practice with those entries using flexible filtering and spaced repetition principles.

## Core Features

### 1. Authentication & User Management

#### Login Options
- **Google OAuth**: Users can sign in with their Google account (OAuth 2.0)
- **Email/Password**: Users can create a local account with email and password
- **Admin Password Login**: A special admin account with a fixed password configured via environment variable (`ADMIN_PASSWORD`). This account always has the Admin role and bypasses the normal user table — it is the bootstrap account for initial setup before any users are created.

#### Roles
| Role | Permissions |
|------|-------------|
| Admin | Full access: create users, delete users, manage all vocabulary data |
| User | Access to own vocabulary entries and practice sessions |

#### Admin Panel
Admins have access to a dedicated `/admin` page with:
- **User list**: View all registered users (name, email, role, date joined, last active)
- **Create user**: Create a new account by entering name, email, role, and temporary password
- **Delete user**: Remove a user and all their associated vocabulary data
- **Promote/demote**: Change a user's role between User and Admin

#### Workflows

**Login via Google:**
1. User clicks "Sign in with Google"
2. Redirected to Google OAuth consent screen
3. On success, redirected back; session created
4. If first-time login, a new User account is provisioned automatically

**Login via email/password:**
1. User enters email and password
2. System validates credentials
3. On success, session created; on failure, error shown

**Admin password login:**
1. User enters the reserved admin username (e.g., `admin`) and the password set via `ADMIN_PASSWORD` env var
2. System authenticates against the env var — no database lookup
3. Session is granted with Admin role
4. This account does not appear in the user list and cannot be deleted

**Admin creates a user:**
1. Admin navigates to `/admin` → "Create User"
2. Enters name, email, role
3. System creates account; user receives email invite to set password

**Admin deletes a user:**
1. Admin navigates to `/admin` → user row → "Delete"
2. Confirmation dialog shown
3. On confirm, user account and all their vocabulary entries are permanently removed

### 2. Data Entry Page

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

### 3. Practice/Review Page

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

### 4. Problematic Words Tracking

The system automatically identifies and surfaces words a user struggles with:

- A word is flagged as **problematic** when the incorrect/need-review rate exceeds a threshold (default: ≥ 40% incorrect over ≥ 3 reviews)
- A dedicated **"Problem Words"** filter on the Practice page shows only flagged entries
- Each vocabulary entry displays a visual indicator (e.g., red badge) when flagged
- The flag clears automatically once the user achieves 3 consecutive correct answers
- Users can also manually flag or unflag any word

Tracked per entry in `review_stats`:
- `times_reviewed`, `correct_count`, `consecutive_correct`, `is_problematic`

### 5. Import & Export

Users can move vocabulary data in and out of the application in multiple formats.

#### Export
Available from the vocabulary list page and the admin panel:
- **CSV** — one row per entry, columns match the data schema fields
- **TSV** — tab-separated equivalent of CSV
- **Excel** (`.xlsx`) — formatted spreadsheet with one sheet per lecture
- **JSON** — full entry objects including review stats

Scope options: export all entries, entries from a specific lecture, or a filtered/selected subset.

#### Import
Available from the data entry page:
- Accepts CSV, TSV, Excel, and JSON files
- Column headers must match field names (case-insensitive); unrecognised columns are ignored
- Duplicate detection: if a word already exists in the same lecture, the user is prompted to skip or overwrite
- Import preview shown before confirming (row count, detected columns, first 5 rows)
- Import errors (missing required fields, malformed rows) are reported per-row; valid rows still import

#### File Format Reference

| Format | Import | Export | Notes |
|--------|--------|--------|-------|
| CSV | Yes | Yes | UTF-8 with BOM for Excel compatibility |
| TSV | Yes | Yes | UTF-8 |
| Excel (.xlsx) | Yes | Yes | `openpyxl`; one sheet per lecture on export |
| JSON | Yes | Yes | Array of entry objects |

### 6. Statistics Dashboard

A `/stats` page shows per-user learning progress:
- Total words added, total reviewed, overall accuracy
- Words learned (3+ consecutive correct) vs. still learning
- Most problematic words (lowest accuracy)
- Review activity over time (chart: reviews per day/week)
- Breakdown by lecture

### 7. Spaced Repetition

The practice engine uses the SM-2 algorithm to schedule reviews:
- Each entry has a calculated next-review date based on performance history
- A **"Due Today"** filter on the Practice page shows entries scheduled for review
- Interval and ease factor stored per entry in `review_stats`
- Manual override: user can force-review any word regardless of schedule

### 8. Multiple Language Pairs

Users are not limited to a single source/target language pair:
- Each vocabulary entry has a `target_language` field (e.g., `fr`, `de`, `ja`)
- The practice page can filter by target language
- TTS uses the correct locale for the selected target language
- Each user can have entries across multiple target languages simultaneously

### 9. Image & Example Associations

Vocabulary entries can include an optional image:
- User uploads an image or provides a URL when adding/editing an entry
- Image displayed alongside the word on the practice card
- Stored in `data/images/` as `<entry_id>.<ext>`; max 2 MB per image

### 10. Cloud Backup

Users can back up and restore their vocabulary data:
- Manual export to a single `.vocabmorizer` backup file (JSON archive)
- Manual import/restore from a backup file
- Optional scheduled backup to a user-configured destination (local path or S3-compatible storage)
- Backup includes all entries and review stats; excludes passwords and OAuth tokens

### 11. Audio/Text-to-Speech

All vocabulary entries support audio playback:
- Click speaker icon on any word to hear pronunciation
- Click speaker icon on usage examples to hear full sentence
- Uses browser's Web Speech API or external TTS service
- Locale for TTS is determined by the entry's `target_language` field

### 12. Localisation (i18n)

The application interface is fully translated into five languages:

| Code | Language |
|------|----------|
| `en` | English (default) |
| `hr` | Croatian |
| `es` | Spanish |
| `pl` | Polish |
| `uk` | Ukrainian |

- A language selector (dropdown or flag icons) is visible in the navigation bar on every page
- The selected language is persisted per user account (stored in the user profile)
- For unauthenticated users, the preference is stored in a browser cookie
- All UI strings — labels, buttons, error messages, navigation, admin panel — are translated
- Vocabulary content itself (words, meanings, usage examples) is not translated — it is user-entered data
- Translation files stored as `locales/<code>/messages.po` (gettext format)

### 13. Data Persistence

All data stored in a local SQLite database (`data/vocabmorizer.db`):
- Single file, no server required
- Supports relational linking of vocabulary entries to user accounts
- No cloud upload by default — all data stays local to the host machine

## Data Schema

### User

```json
{
  "id": "uuid",
  "name": "Jane Smith",
  "email": "jane@example.com",
  "role": "user",
  "auth_provider": "google",
  "google_id": "google-oauth-sub-id",
  "password_hash": null,
  "date_joined": "2026-05-06",
  "last_active": "2026-05-06",
  "preferred_language": "en"
}
```

- `auth_provider`: `"google"` or `"local"`
- `google_id`: populated only for Google OAuth users
- `password_hash`: populated only for local email/password accounts

### Vocabulary Entry

```json
{
  "id": "uuid",
  "user_id": "uuid",
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
  "target_language": "fr",
  "image_path": "data/images/<entry_id>.jpg",
  "review_stats": {
    "times_reviewed": 5,
    "correct_count": 3,
    "consecutive_correct": 1,
    "is_problematic": false,
    "ease_factor": 2.5,
    "interval_days": 3,
    "next_review_date": "2026-05-09",
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
- i18n: `Flask-Babel` (gettext) for server-rendered strings; language switcher in navbar

### Backend
- Language: Python
- Data storage: SQLite (required for multi-user with relational user↔vocabulary links)
- Authentication: Google OAuth 2.0 via `authlib` or `google-auth`; local accounts with `bcrypt` password hashing; admin password via `ADMIN_PASSWORD` environment variable
- Session management: server-side sessions with `flask-login` or equivalent
- Admin routes protected by role check middleware
- i18n translation files: `locales/<code>/LC_MESSAGES/messages.po` (gettext); languages: `en`, `hr`, `es`, `pl`, `uk`
- Import/export: `openpyxl` for Excel, standard library `csv` for CSV/TSV, `json` for JSON
- Spaced repetition: SM-2 algorithm implemented in-app (no external dependency)

### Browser Compatibility
- Modern browsers with Web Speech API support (Chrome, Firefox, Safari, Edge)
- No specific mobile responsiveness required (desktop-first)

## Non-Goals

- Multimedia pronunciation library (using system TTS only)
- Social features or community sharing
- Mobile app (web-based only)
- Real-time collaboration
- Advanced NLP processing
