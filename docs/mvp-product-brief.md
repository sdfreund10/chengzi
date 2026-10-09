# Product Brief: Chinese Flashcard Trainer

> **Note:** This is an initial guideline, not a firm requirement. The brief should guide the high-level product and its outcomes, but deviations are expected over time as the app is built and used.

A private PWA for two people to drill Traditional Chinese vocabulary with spaced-repetition flashcards. Practice one deck at a time (about 100 words, 10 to 20 seconds per card) using taps only. Mockups: `chinese-flashcards-mockups.html`.

## Goals
- Effortless, one-handed practice on a phone.
- Independent progress for each person on one shared word list.
- Harder study modes unlock only once a word is known well.
- Instant feel: the session's deck loads up front, so there's no waiting between cards.
- **Success:** both of us practice several times a week.

**Non-goals (v1):** public signup, audio, handwriting, gamification, per-user words, simplified characters, offline study, native apps.

## Stack
| Layer | Choice |
|---|---|
| Backend | Python, Django, typed API layer (e.g., django-ninja), Postgres |
| Frontend | Preact + TypeScript, installable PWA (online-first) |
| Auth | Same-origin session cookies, two seeded accounts |
| Scheduling | Server-authoritative; the client only orders the session |

## Data model
| Entity | Fields and notes |
|---|---|
| **Word** (shared) | `chinese` (traditional), `pinyin` (tone marks), `english_basic` |
| **Category** (a "deck") | Many-to-many with Word. In v1, one deck per HSK level |
| **User** | Login only |
| **UserWord** | One row per (user, word, mode), unique. `mode`, `easy_streak` (resets on hard), `easy_count` (never resets), `due_on` (date), `last_practiced_at` |

Rows are created lazily: the first time a user practices a deck, `pinyin_to_en` rows are created for all its words. Other modes are created when unlocked.

## Study modes
| Mode | Prompt | Answer (in order) |
|---|---|---|
| Pinyin to English | Pinyin | Basic English, characters |
| English to Chinese | Basic English | Characters, pinyin |
| Characters to English | Characters | Basic English, pinyin |

**Unlocking** (per word, per user, using `easy_count` with a threshold of 5):
1. Pinyin to English is available from the start.
2. English to Chinese unlocks when Pinyin to English reaches the threshold.
3. Characters to English unlocks when both others have.

Unlocks are permanent. A new mode's first `due_on` is tomorrow.

## Scheduling
`due_on` only decides which cards are in today's session; it isn't a literal deadline. There's no day-rollover logic.

| Tap | Result |
|---|---|
| Hard (left) | `due_on` = today; `easy_streak` = 0; `easy_count` unchanged |
| Easy (right) | `easy_streak` + 1, `easy_count` + 1; next due by new streak: **1** = tomorrow, **2 to 4** = 3 days, **5 to 9** = 7 days, **10+** = 14 days |

**Session:**
- Deck = the user's cards in the chosen deck with `due_on` today or earlier, across unlocked modes, shuffled.
- At most one mode per word per session, so one answer never gives away another.
- Easy: the card leaves the session. Hard: it's reinserted at a random position.
- The session ends when the deck is empty.

Ladder intervals and the unlock threshold are hard-coded in the settings file. Early sessions with the largest HSK levels will be long; deck sizes will be tuned after real use.

## Screens
Light theme: background `#FAFAF7`, text `#1E2024`, pinyin accent `#2F5BD9`, hard zone `#FBE4E4`, easy zone `#E1F3E6`.

| Screen | Behavior |
|---|---|
| Login | Username and password. No registration |
| Deck picker | List of decks with word count and a "N due" badge (quieter "None due" when empty). Tap to start |
| Study card | Mode chip and counter on top, large prompt. **Tap anywhere** to reveal. Then **left half = hard, right half = easy** (tinted zones, whole halves tappable). Advances immediately, with no confirmation |
| All caught up | Short message and a button back to the deck picker |

## Content
- **Source:** HSK 3.0 from the open `complete-hsk-vocabulary` dataset, using each level's *new* words so every word sits in the level where it's introduced. Traditional forms, pinyin, and meanings come from the data.
- **Import report:** polyphones, multi-definition entries, and per-level counts versus the official syllabus (the dataset's 3.0 coverage may have gaps).
- **Edits:** corrections through Django admin. No manual word entry in v1.
- **Known quirk:** Pinyin to English can be ambiguous (homophones). The answer shows characters too.

## Scope
| Release | Contents |
|---|---|
| **v1** | Login, HSK 3.0 import, data corrections, three study modes, streak/count scheduling, deck picker, study card, all-caught-up screen, installable PWA |
| **v1.1** | Manually added words (with CSV import), auto-categorization |
| **v1.2** | LLM-generated details and example sentences, with a collapsed detail section |
| **Unscheduled** | Draft/reviewed status, undo, session summary, remembering last deck, offline study, text-to-speech, stats view, dark theme, smaller decks, daily new-word cap, longer intervals |

## Open items
- Tune deck sizes after real use.
- Consider unlocking Characters to English earlier. It's usually the easiest direction, so unlocking it last gives character recognition the least practice.