# Learning And Review Redesign Design

**Goal**

Redesign the Android app so search remains the default home page, learning becomes a dedicated staged quiz flow, starred words move into their own module, review reads only from words actually learned in the learning module, and dictionary installation correctly replaces old sample databases with the full packaged database.

## Scope

This design covers:

- fixing packaged dictionary install detection so old sample databases are not reused
- keeping search as the default first tab
- adding a dedicated starred module that is separate from learning and review
- replacing the current learning tab with a two-stage ten-word learning session
- redefining review to read only learned words whose review time is due
- using the device clock to schedule reviews with an Ebbinghaus-like interval ladder

This design does not cover:

- online sync
- account systems
- cloud backup
- adaptive difficulty beyond the first fixed interval model
- handwriting input
- voice input

## Product Structure

The app will expose four bottom-navigation modules:

1. Search
2. Learning
3. Starred
4. Review

Search stays the default entry point.

The old learning-card flow is removed as a primary product path. Learning becomes a session-based quiz experience. Review becomes a due-queue over learned words only. Starred words are managed separately and do not automatically enter learning or review.

## Navigation Layout

Bottom navigation order:

- leftmost: Search
- left-middle: Learning
- right-middle: Starred
- rightmost: Review

The user's wording emphasized learning at the lower left and review at the lower right. This layout satisfies that while still leaving room for the new starred module.

## Data Model Boundaries

The app will maintain three separate user-data concerns:

### 1. Starred Records

Purpose:

- persist words the user manually favorites from search or detail

Rules:

- star state is independent of learning
- starred words do not automatically enter review
- un-starring does not affect learning history

### 2. Learning Progress Records

Purpose:

- persist whether a word has entered and completed the learning flow

Required fields:

- `word_id`
- `language`
- `learning_state`
- `choice_correct_count`
- `choice_wrong_count`
- `spelling_correct_count`
- `spelling_wrong_count`
- `hint_used_count`
- `last_learned_at_millis`
- `next_review_at_millis`
- `review_stage`

### 3. Active Session State

Purpose:

- hold the in-progress ten-word learning session in memory

Rules:

- session state is UI/session scoped
- persistent learning records are only updated at meaningful milestones
- incomplete session state does not need full long-term persistence in the first version

## Dictionary Install Fix

Current issue:

- the installer can treat an old sample dictionary as compatible with the packaged full dictionary because it compares only schema version, database filename, and FTS capability

Required fix:

- installer compatibility must also compare `entry_count`
- if packaged manifest and installed manifest disagree on entry count, reinstall the packaged assets

Recommended extension:

- keep the current checks
- add `entry_count`
- optionally add a future field for package version or checksum, but that is not required for this implementation

Expected result:

- reinstalling the app or launching after upgrade should replace old sample data with the packaged full dictionary

## Learning Module Design

### Entry

When the user enters Learning:

1. choose language: Japanese or French
2. request a fresh session of 10 words from that language
3. source words must be words that have not yet completed learning

If fewer than 10 unlearned words are available:

- start with as many as are available

### Session Shape

Each learning session has two stages:

1. meaning-choice stage
2. spelling stage

The user must complete the first stage for all ten words before entering the second stage.

### Stage 1: Meaning Choice

For each question:

- show the foreign-language spelling only
- show four Chinese meanings labeled A/B/C/D
- exactly one option is correct
- three options are distractors

Correct-answer behavior:

- mark the current question correct
- move forward to the next unanswered or unresolved word

Wrong-answer behavior:

- visibly mark the mistake
- keep the word in the current ten-word session
- the user must see this word again later in the same stage until it has been answered correctly at least once

Completion rule for stage 1:

- stage 1 finishes only when all words in the session have been answered correctly at least once

### Distractor Rules

Distractors should:

- come from the same language where possible
- use Chinese meanings from other entries
- avoid duplicating the exact correct Chinese meaning

First version simplification:

- random same-language distractors are acceptable if exact duplicates are filtered out

### Stage 2: Spelling

After all ten words clear stage 1:

- present each word again using the Chinese meaning
- require the user to type the full foreign-language spelling

Prompt rules:

- Japanese: the expected answer is the stored spelling form from the dictionary entry
- French: the expected answer is the stored spelling form from the dictionary entry

Answer evaluation:

- exact match after simple whitespace trim
- no fuzzy spelling acceptance in the first version

### Hint Button

The spelling screen includes a hint button.

Hint behavior:

- Japanese: reveal reading or phonetic form
- French: reveal IPA when available, otherwise reveal the first letter
- if IPA is shown for French and the entry has no IPA, fall back to first-letter hint

Hint usage must be counted in the learning record.

### Learning Completion

A word is considered learned for first-pass scheduling when:

- it has cleared the meaning-choice stage
- it has been attempted in spelling stage

Scheduling rule:

- once the session is completed, each word in the session receives:
  - updated learning counters
  - `last_learned_at_millis`
  - initial `review_stage`
  - calculated `next_review_at_millis`

## Review Module Design

Review reads only from words learned through the learning module.

Starred words are excluded unless they later become learned through learning.

### Due Queue

When the user enters Review:

- read current device time
- query learned words where `next_review_at_millis <= now`
- order by oldest due time first

### Review Question Flow

Review reuses the same two knowledge checks:

1. meaning-choice
2. spelling

For the first implementation, review may present both checks sequentially for one word before advancing.

Success behavior:

- advance the review stage
- compute the next review time

Failure behavior:

- reduce or reset the review stage
- schedule an earlier next review time

## Review Scheduling Model

The scheduling model should remain simple and deterministic.

Recommended interval ladder:

- stage 0: same day or immediate retry
- stage 1: 1 day
- stage 2: 2 days
- stage 3: 4 days
- stage 4: 7 days
- stage 5: 15 days
- stage 6: 30 days

Behavior:

- fully correct review result advances one stage
- partially wrong result falls back by at least one stage
- strongly wrong result can reset to stage 1 or 0 depending on current state

This is intentionally an Ebbinghaus-style approximation, not a full SM-2 implementation.

## Search Module Changes

Search remains the default homepage.

It still supports:

- query
- result list
- detail view
- speech

Changes:

- remove the idea that adding from search sends a word into learning automatically
- search should instead support starring/un-starring

Optional future extension:

- search detail may expose both star and "learn later" actions, but "learn later" is out of scope here

## Starred Module Design

The new Starred module shows the user's favorited words.

Capabilities:

- list starred words
- open detail
- remove star
- optional speak action

Rules:

- starred words are informational/bookmark oriented
- they do not enter learning or review queues automatically

## Architecture Changes

### UI Layer

Expected screen-level states:

- `SearchUiState`
- `LearningUiState`
- `StarredUiState`
- `ReviewUiState`

Learning UI state must become session-based rather than card-based.

Suggested sub-models:

- `LearningLanguageSelectionState`
- `LearningChoiceQuestionState`
- `LearningSpellingQuestionState`
- `LearningSessionSummaryState`

### Domain Layer

Add dedicated use cases or gateway methods for:

- requesting ten new learning words by language
- generating multiple-choice questions with distractors
- evaluating choice answers
- evaluating spelling answers
- starring and unstarring words
- listing starred words
- loading due review words
- applying review outcomes to schedule

### Data Layer

Add or extend local stores for:

- learning progress records
- starred records

The dictionary database remains read-only for source word content. User progress remains in app-private local storage.

## Error Handling

Learning:

- if fewer than 10 words are available, start with fewer rather than fail
- if distractors cannot be generated cleanly, degrade to any non-duplicate Chinese meanings from the same language

Review:

- if no words are due, show a clear empty state

Search and Starred:

- missing details should not crash the app

Install:

- if manifest mismatch or database missing, reinstall packaged assets

## Testing Strategy

### Unit Tests

- installer reinstalls when entry count changes
- learning session generator returns only unlearned words of selected language
- choice-question generator always includes one correct answer and no duplicate options
- wrong choice answers keep the word in the current session
- spelling hints return the expected reading/IPA/first-letter behavior
- review scheduling advances and falls back correctly by stage
- starred store remains independent from learning progress

### UI Tests

- search remains the default tab
- bottom navigation shows Search, Learning, Starred, Review
- learning flow transitions from language selection to choice stage to spelling stage
- review due queue renders empty and populated states correctly
- starred list renders and removes items correctly

### Smoke Validation

- install on device with previously installed sample database now migrates to the full packaged database
- learning session can be completed end to end
- finished session produces due review records
- starred words stay out of review until actually learned

## Implementation Notes

To keep scope controlled:

- reuse existing app shell and bottom navigation
- reuse dictionary lookup/repository logic where possible
- replace, rather than layer on top of, the old learning-card behavior
- keep review scheduling simple and table-driven

## Acceptance Criteria

The redesign is successful when:

- the app opens on Search
- the app exposes four tabs: Search, Learning, Starred, Review
- old sample installs are replaced with the packaged full dictionary
- Learning starts from language selection and runs a ten-word session
- wrong meaning-choice answers reappear inside the same session
- spelling phase supports a hint button
- completed learning sessions create reviewable records
- Review shows only learned due words
- Starred words remain a separate module and do not automatically enter learning or review
