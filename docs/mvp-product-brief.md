# Product Brief: Chinese Flashcard Trainer

> **Note:** This is an initial guideline, not a firm requirement. The brief should guide the high-level product and its outcomes, but deviations are expected over time as the app is built and used.

## 1. Overview

A small, private web app for two people to drill Traditional Chinese vocabulary. It is optimized for speed and low friction: open it, pick a deck, tap through cards, and let the scheduler decide which words show up. It is built for personal use, so it skips public signup, onboarding, social features, and monetization.

Interactive mockups of the v1 screens live in `chinese-flashcards-mockups.html`.

## 2. Goals and non-goals

**Goals**
- Make a regular practice session effortless, ideally one-handed on a phone.
- Review one deck at a time (roughly 100 words, around 10 to 20 seconds per card).
- Let each person progress independently on one shared word list.
- Introduce difficulty gradually: a word unlocks harder study modes only once it is known well.

**Non-goals (v1)**
- Public signup, password reset, multi-tenant concerns
- Audio, handwriting, stroke order
- Gamification (streaks, leaderboards)
- Per-user word lists
- Simplified characters
- Offline study and native apps

## 3. Tech stack

- **Backend:** Python with Django and a typed API layer (such as django-ninja), on Postgres.
- **Frontend:** Preact with TypeScript, built as an installable PWA. The study loop is stateful and client-side, which is why a client app is justified.
- **Auth:** same-origin session cookies. The built frontend and the API are served under one domain.
- **Scheduling is server-authoritative.** The client only handles in-session ordering.
- **Online-first PWA for v1.** Installable with a cached app shell; offline study can come later.

## 4. Core concepts

### Word (shared by both users)
- `chinese`: traditional characters
- `pinyin`: with tone marks (nǐ hǎo), not tone numbers
- `english_basic`: a short gloss used on cards

### Category (a "deck")
A named grouping of words. In v1, each HSK level is one deck. Words can belong to several categories (many-to-many).

### User
A login only. Each user has independent progress.

### UserWord
Per-user learning state, **one row per (user, word, mode)**, with a uniqueness constraint on that combination.
- `mode`: `pinyin_to_en`, `en_to_zh`, or `zh_to_en`
- `easy_streak`: consecutive easy taps; reset to 0 by any hard tap. Drives scheduling intervals.
- `easy_count`: total easy taps, never reset. Drives mode unlocking.
- `due_on`: a date used to decide which cards belong in a session
- `last_practiced_at`: a timestamp, kept for later use

**Lazy row creation:** rows are created the first time a user practices a deck, not for the whole word list. On first practice, `pinyin_to_en` rows are created for all words in that deck. Rows for the other modes are created when unlocked.

## 5. Study modes and unlocking

| Mode | Prompt | Answer shows (in order) |
|---|---|---|
| Pinyin to English | Pinyin | Basic English, then characters |
| English to Chinese | Basic English | Characters, then pinyin |
| Characters to English | Characters | Basic English, then pinyin |

**Unlock chain (per word, per user)**
1. `pinyin_to_en` is available from the start.
2. `en_to_zh` unlocks when the word's `pinyin_to_en` `easy_count` reaches the threshold (5).
3. `zh_to_en` unlocks when both of the other modes have reached the threshold.

Unlocks are permanent: `easy_count` never decreases, so a later hard tap never relocks a mode. A newly unlocked mode's first `due_on` is tomorrow, so it doesn't land alongside its sibling card in the same session.

A session is a **mixed queue** across all of a deck's unlocked modes, with at most one mode per word per session so one answer never gives away another.

## 6. Scheduling

`due_on` is not a literal deadline. It is a simple signal for building each session's deck: a card is in the deck if its `due_on` is today or earlier. There is no day-rollover logic; "today" is just the calendar date.

### Rating a card
Two ratings only: hard (left tap) and easy (right tap).

| Event | Result |
|---|---|
| Hard tap | `due_on` = today; `easy_streak` = 0; `easy_count` unchanged |
| Easy tap | `easy_streak` + 1 and `easy_count` + 1; `due_on` = today + the interval for the new streak |

| `easy_streak` after tap | Next due |
|---|---|
| 1 | Tomorrow |
| 2 to 4 | 3 days |
| 5 to 9 | 7 days |
| 10 or more | 14 days |

### Building and running a session
- **Deck:** all of the user's rows in the selected deck with `due_on` today or earlier, across unlocked modes, shuffled at the start.
- **Easy tap:** the card leaves the session.
- **Hard tap:** the card is reinserted at a random position in the remaining cards.
- **Session end:** the deck is empty, meaning every card has had an easy tap.
- Missing days simply makes the next deck bigger.

### Tunable values
The ladder intervals and the unlock threshold (5) are hard-coded in the settings file for v1. Early sessions with the largest HSK levels will be long; deck sizes are expected to be tuned after real use.

## 7. UX and screens

**Visual direction:** a simple, typography-led layout with a large prompt, a mode chip and counter at the top, and two color-tinted tap zones, in a light theme.
- Background `#FAFAF7`, text `#1E2024`, muted text `#7A808A`
- Pinyin accent `#2F5BD9`
- Hard zone `#FBE4E4` (text `#A32D2D`); easy zone `#E1F3E6` (text `#1F6B3A`)

### Login
Minimal username and password form for two seeded accounts. No registration flow.

### Deck picker
A bordered list of decks (HSK levels), each showing its word count and a badge with the number of cards due. Decks with nothing due show a quieter "None due" badge. Tapping a deck starts a session.

### Study card
- **Top bar:** mode chip (e.g., "English to Chinese") and a progress counter.
- **Prompt:** large and centered, with a faint "Tap anywhere to reveal" hint.
- **Tap 1, anywhere:** reveals the answer in the order shown in section 5.
- **After reveal:** the bottom of the screen shows a left "Hard" zone and a right "Easy" zone. The entire left and right halves of the screen are tappable.
- **Tap 2:** advances to the next card immediately, with no confirmation message.

### All caught up
Shown when a deck has no due cards: a short message and a button back to the deck picker.

## 8. Content

**Source:** the HSK 3.0 vocabulary from the open `complete-hsk-vocabulary` dataset, using the lists of new words per level so each word belongs to the level where it is introduced. Traditional forms, pinyin, and English meanings come from the dataset.

**Import checks:** report polyphones (words with more than one pronunciation), entries with several definitions, and per-level word counts compared with the official syllabus, since the dataset's 3.0 coverage may be slightly incomplete. The import should choose the best single basic gloss per word.

**Editing:** imported words can be corrected through Django's admin. There is no manual word entry in v1.

## 9. Edge cases
- Nothing due: show the "All caught up" screen.
- Pinyin to English can be ambiguous because of homophones; the answer shows characters too, and this is an accepted quirk of the mode.
- A word in several decks has one UserWord row per mode, not one per deck.

## 10. Success criteria
- Both users practice several times a week.
- Revealing and rating feel instant: the session's deck is loaded at the start so there is no loading between cards.

## 11. Scope

**v1**
1. Two-user login
2. HSK 3.0 import, one deck per level
3. Word and deck management for correcting data
4. Three study modes with tap-to-reveal and left/right rating
5. Streak-driven intervals and count-based mode unlocking
6. Deck picker, study card, and "All caught up" screens (light theme)
7. Installable PWA

**v1.1:** manually added words (with CSV import), auto-categorization

**v1.2:** LLM-generated extra details and example sentences, with a collapsed detail section on the answer side

**Unscheduled:** draft/reviewed status for words, undo, a session summary, remembering the last deck selection, offline study, text-to-speech, a stats view, a dark theme, smaller decks, a daily new-word cap, longer review intervals, a "regenerate details" button

## 12. Open items
- Tuning deck sizes after real use.
- Whether to unlock Characters to English earlier in the chain. It is usually the easiest direction, so placing it last gives character recognition the least practice.
