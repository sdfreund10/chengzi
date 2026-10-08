# Product Brief: Chinese Flashcard Trainer

## 1. Overview

A small, private web app for two people to drill Traditional Chinese vocabulary. It is optimized for speed and low friction: open it, pick a category, tap through cards, and let the scheduler decide what comes next. It is built for personal use, so it skips public signup, onboarding, social features, and monetization.

## 2. Goals and non-goals

**Goals**

- Make a daily 5-10 minute practice session effortless, ideally one-handed on a phone.
- Surface the right cards at the right time using spaced repetition.
- Let each person progress independently on one shared word list.
- Introduce difficulty gradually: each word unlocks harder study modes only once it is known well.

**Non-goals (v1)**

- Public signup, password reset flows, multi-tenant concerns
- Audio, handwriting, stroke order
- Gamification (streaks, leaderboards)
- Per-user word lists
- Simplified characters
- Native apps (a mobile-friendly web app is enough)

## 3. Core concepts and data model

### Word (shared by both users)

| Field | Notes |
| --- | --- |
| `chinese` | Traditional characters |
| `pinyin` | With tone marks (nǐ hǎo), not tone numbers |
| `english_basic` | Short gloss used on the card prompt and answer |
| `english_detail` | "Complex definition": nuance, multiple senses, usage notes. Shown on the answer side, de-emphasized or collapsed |
| `sentence_zh` | Example sentence, traditional characters |
| `sentence_pinyin` | Same sentence with tone marks |
| `sentence_en` | English translation |
| `review_status` | `draft` or `reviewed` (see Content authoring) |

The three sentence fields are required together or not at all.

### Category

A named grouping (e.g., Places, Food). Many-to-many with Word through a `word_category` join. A word may belong to several categories.

### User

A login only. Each user has independent progress.

### UserWord

Per-user learning state, **one row per (user, word, mode)**. A unique constraint on `(user_id, word_id, mode)` prevents duplicates when a word appears in several categories.

| Field | Notes |
| --- | --- |
| `mode` | `pinyin_to_en`, `en_to_zh`, or `zh_to_en` |
| `easy_streak` | Consecutive easy taps; reset to 0 on any hard tap. Drives scheduling intervals |
| `easy_count` | Total easy taps ever for this row; never reset. Drives mode unlocking |
| `due_on` | A calendar date, not a timestamp |
| `last_practiced_at` | Real timestamp, kept for stats |

### Lazy row creation

Rows are never created for the whole word list. The first time a user practices a category, `pinyin_to_en` rows are created for that category's words (due today). Rows for the other modes are created only when unlocked.

## 4. Study modes and unlocking

| Mode | Prompt | Answer reveals (in order) |
| --- | --- | --- |
| Pinyin to English | Pinyin | Basic English, characters, then detail and sentence |
| English to Chinese | Basic English | Characters, pinyin, then detail and sentence |
| Characters to English | Characters | Basic English, pinyin, then detail and sentence |

**Unlock chain (per word, per user)**

1. `pinyin_to_en` is available from the start.
2. `en_to_zh` unlocks when the word's `pinyin_to_en` row reaches the unlock threshold on `easy_count` (default 5).
3. `zh_to_en` unlocks when both the `pinyin_to_en` and `en_to_zh` rows have reached the threshold.

**Rules**

- A newly unlocked mode's first `due_on` is **tomorrow**, which keeps sibling cards for the same word from landing in the same session.
- Unlocks are permanent: `easy_count` never decreases, so a later hard tap never relocks a mode.
- Unlock check runs on each easy tap. When `easy_count` crosses the threshold and the chain's prerequisites are met, the next mode's row is created with `due_on` = tomorrow.
- Sessions use a **mixed queue** across all unlocked modes for the selected categories.
- Sibling-leak rule: show at most one mode per word per day, since seeing one mode's answer gives away another.

## 5. Scheduling

### Principles

- Two ratings only: hard (left tap) and easy (right tap).
- Resolution is by **day**: "today" and "tomorrow". No minute-level timers.
- The ladder is fixed. Values live in one config so they can be tuned from real use.

### Ladder

Two counters on each UserWord do different jobs:

- **`easy_streak`** (reset by any hard tap) decides **how far out the card is scheduled**.
- **`easy_count`** (never reset) decides **when the next mode unlocks**.

| Event | Result |
| --- | --- |
| Hard tap | `due_on` = today; `easy_streak` = 0; `easy_count` unchanged |
| Easy tap | `easy_streak` + 1 and `easy_count` + 1; `due_on` = today + the interval for the new streak (below) |

**Streak-to-interval ladder (defaults, one config array)**

| `easy_streak` after tap | Next due |
| --- | --- |
| 1 | Tomorrow |
| 2 to 4 | 3 days |
| 5 to 9 | 7 days |
| 10 or more | 14 days |

**Mastered is derived, not stored.** A row counts as "mastered" for display (category picker counts, session summary) when `easy_streak` is at or above a configured level (default 5). A hard tap resets the streak, so the card naturally drops out of mastered with no separate flag to maintain.

**Why cumulative count for unlocking:** a hard tap should send a card back to short intervals, but it shouldn't take away a mode the user already earned. Because an easy tap removes the card from today's queue, `easy_count` can grow at most once per day per row in normal use, so reaching 5 means the word was recalled on five separate days, though not necessarily consecutively. Each mode's counters are independent.

### Session queue

- **Query:** all of the user's rows where `due_on <= today`, filtered to unlocked modes and selected categories. Overdue cards are included automatically.
- **New cards:** words in a selected category without a row yet get `pinyin_to_en` rows on first practice. A per-session cap limits how many new cards are shown.
- **Easy tap:** the card leaves this session's queue (it is now due tomorrow or later).
- **Hard tap:** the card is reinserted *k* positions ahead in the in-memory queue, where *k* is roughly a quarter of the remaining queue with a floor of about 3. The database only records `due_on = today`; there is no within-session timer.
- **Session end:** the queue is empty, meaning every card has received an easy tap.
- **Practice ahead:** if nothing is due, the user can optionally practice cards not yet due.

### Day boundary

"Today" rolls over at a configured early-morning hour (default 4 a.m.) so late-night sessions count as the previous day. One configured timezone is enough for v1 since both users share it.

### Workload note

At full scale (1,000 words x 3 modes per person), a 14-day mastered cadence is roughly 215 reviews per day per person. That steady state will take months to reach because words are introduced category by category. A 30-day rung can be added later with no structural change.

## 6. UX and screens

**Visual direction:** the "split zone" layout in a light theme: a simple, typography-led screen with large prompts, a mode chip and counter at the top, and two color-tinted tap zones.

**Light palette used in mockups**

- Screen background `#FAFAF7`, text `#1E2024`, muted text `#7A808A`
- Chip fill `#EEF0F2`, hairlines `#D9DCE0`
- Pinyin accent `#2F5BD9`
- Hard zone `#FBE4E4` with text `#A32D2D`; easy zone `#E1F3E6` with text `#1F6B3A`

### Login

Minimal email and password form. Two accounts; no registration flow in v1.

### Category picker

- Header "Choose what to practice", with a note that modes are mixed automatically.
- Bordered list rows (not cards), each with a checkbox, category name, word count, mastered count, and a status badge: "N due", "None due" (muted, still selectable for practicing ahead), or "New".
- Primary button at the bottom shows the actual session size: "Start session · 15 cards".

### Study card

- **Top bar:** mode chip (e.g., "English to Chinese") and progress counter (e.g., "7 / 20").
- **Prompt:** large and centered. A faint "Tap anywhere" hint sits at the bottom.
- **Tap 1, anywhere:** reveals the answer in the order defined for the mode. The detail definition is collapsed or de-emphasized; the example sentence shows in characters, pinyin, and English.
- **Zones appear on reveal:** the bottom of the screen splits into a left "Hard / later today" zone and a right "Easy / tomorrow" zone. The **entire left and right halves** of the screen are tappable, not just the tinted areas.
- **Tap 2:** a brief confirmation ("Hard · back today" or "Easy · see you tomorrow") then the next card.
- **Undo:** a lightweight undo for the last rating, since mis-taps are likely.

### Session summary

- Cards reviewed, with a Hard / Easy split in the zone colors.
- Rows for: due tomorrow, newly mastered words, and any new mode unlocked.
- Buttons: "Practice again" and "Done".

### Empty state: "All caught up"

Names what happened, states when the next cards are due, and offers a "Practice ahead" action and a category picker.

## 7. Content authoring

### Seeding (1,000 most common words)

- **Skeleton from a dictionary:** take traditional characters, pinyin, and basic gloss from an open dictionary (such as CC-CEDICT) plus a frequency list. These fields should be reliable.
- **LLM for finer details:** generate `english_detail`, the three-script example sentence, and suggested categories.
- **Validation:** compare generated pinyin for single words against the dictionary and flag mismatches. LLMs make real mistakes with polyphonic characters inside sentences (e.g., 了, 行), so generated content starts as `draft`.

### Auto-categorization

Keep a fixed, human-curated category list. Have the LLM propose one to three categories per word **from that list only**, marked pending until approved. The specific tool for this (a "decision engine" under consideration) is still to be chosen; the controlled-vocabulary-plus-approval pattern works with any.

### Management UI (v1 minimum)

- Word list with search and filters for category and review status (including "needs review").
- Edit form for all word fields.
- Category create, rename, and assignment.
- CSV import: `chinese`, `pinyin`, `english_basic`, `english_detail`, `sentence_zh`, `sentence_pinyin`, `sentence_en`, and a delimited `categories` column.
- Per-word "regenerate details" action.

## 8. Edge cases

- Nothing due: show the empty state with practice-ahead option.
- Pinyin to English can be ambiguous because of homophones; the answer shows characters too, and this is an accepted quirk of the mode.
- Category and session selections are remembered between sessions.
- A word in several categories has one UserWord row per mode, not one per category.
- Missing a day simply grows tomorrow's queue.

## 9. Success criteria

- Both users practice several times a week.
- Reveal and rate feel instant: prefetch the due queue at session start so there is no loading between cards.
- Draft content gets reviewed over time (a visible "needs review" count trends down).

## 10. v1 scope

1. Two-user login
2. Word and category management (CRUD plus CSV import), with review status
3. Seeded word list (1,000 words)
4. Three study modes with tap-to-reveal and left/right rating
5. Day-based ladder scheduler (streak-driven intervals) with count-based mode unlocking
6. Category picker, study card, and session summary screens (light theme)
7. All-caught-up empty state

**Later ideas:** text-to-speech, tone-colored characters, stats view, leech flag for repeatedly missed words, 30-day rung, dark theme, simplified-character option, installable PWA with offline support.

## 11. Tunable parameters and open items

| Parameter | Default | Notes |
| --- | --- | --- |
| `easy_count` threshold to unlock the next mode | 5 | Cumulative, never reset; at most one increment per day per row, so about five days minimum |
| Streak-to-interval ladder | 1, 3, 7, 14 days at streaks 1, 2-4, 5-9, 10+ | Config array; add a 30-day rung if desired |
| Streak level that displays as "mastered" | 5 | Derived for display only; not stored |
| Hard-card requeue distance | About 1/4 of remaining queue, minimum about 3 | Session-level only |
| New cards per session cap | To be set | Tune based on category sizes |
| Day rollover hour | 4 a.m. | Single configured timezone |

**Open**

- Choice of tool for auto-categorization.
- Whether to move Characters to English earlier in the unlock chain (it is usually the easiest direction, so placing it last gives character recognition the least practice).
- Whether a word's sentence is optional or required for seeded content.