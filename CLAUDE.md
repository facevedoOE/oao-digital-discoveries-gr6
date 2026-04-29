# Claude Code — Digital Discoveries Course Builder
# Paste this as your Claude Code system prompt (or CLAUDE.md in the repo root)

You are building **6th Grade Digital Discoveries**, an asynchronous self-paced
course for Optima Academy Online (OAO), delivered through Canvas LMS.

---

## Your two jobs

1. **Build course content** — HTML reading pages, interactive JS activities,
   and QTI 1.2 quiz files, organized by unit and lesson.

2. **Keep course-config.json in sync** — every time you create, rename, or
   reorganize a file, update course-config.json to match. This config is what
   drives the Canvas deploy script. If the config is out of date, the deploy
   will fail or create the wrong structure.

---

## Repo structure — always follow this exactly

```
OAO-Hope/                          ← repo root
  unit-1/
    lesson-1-1/
      reading.html
      activity.html
      quiz.qti.zip
    lesson-1-2/
      reading.html
      activity.html
      quiz.qti.zip
  unit-2/
    lesson-2-1/
      ...
  canvas_deploy.py                 ← do not modify
  course-config.json               ← YOU must keep this updated
  .gitignore                       ← do not modify
  README.md                        ← update if you add new units
```

File naming rules:
- Folders: `unit-N/lesson-N-M/` (e.g. `unit-1/lesson-1-3/`)
- Reading page: always named `reading.html`
- Interactive activity: always named `activity.html`
- Quiz: always named `quiz.qti.zip`

---

## course-config.json — how to keep it updated

The config lives at the repo root. It is gitignored (credentials inside) so
you will only ever edit it locally — never commit it.

### When you CREATE a new lesson, add a block like this inside the correct unit:

```json
{
  "id": "u1-l3",
  "title": "Lesson 1.3: YOUR LESSON TITLE HERE",
  "items": [
    {
      "type": "reading",
      "title": "Reading: YOUR LESSON TITLE HERE",
      "source": "github",
      "file": "unit-1/lesson-1-3/reading.html",
      "completion_requirement": "must_view"
    },
    {
      "type": "interactive",
      "title": "Activity: YOUR ACTIVITY TITLE HERE",
      "source": "github",
      "file": "unit-1/lesson-1-3/activity.html",
      "completion_requirement": "must_view"
    },
    {
      "type": "quiz",
      "title": "Quiz: YOUR LESSON TITLE HERE",
      "source": "local",
      "file": "unit-1/lesson-1-3/quiz.qti.zip",
      "points_possible": 5,
      "allowed_attempts": 3,
      "completion_requirement": "must_score_at_least",
      "min_score": 3
    }
  ]
}
```

### When you CREATE a new unit, add a block like this to the units array:

```json
{
  "id": "unit-3",
  "title": "Unit 3: YOUR UNIT TITLE HERE",
  "canvas_module_position": 3,
  "unlock_after_unit": "unit-2",
  "lessons": []
}
```

### Rules for editing course-config.json:
- NEVER change the "course" block at the top — credentials live there
- ALWAYS increment canvas_module_position sequentially
- ALWAYS set unlock_after_unit to the previous unit's id (or null for unit 1)
- ALWAYS match "file" paths exactly to the actual file you created
- ALWAYS update the config in the same commit/session as the files it describes

---

## OAO Design System

### Brand colors
- Binary Blue:    #0E1C42  (dark navy — primary background)
- Bitstream Blue: #55C8E8  (bright blue — accents, links)
- Gateway Gold:   #C7922C  (gold — highlights, achievements)
- Portal Purple:  #67308F  (purple — secondary accent)
- Gamer Green:    #76C043  (green — success states)
- Odyssey Orange: #F78F1E  (orange — interactive elements)

### Fonts
Wix Madefor Display (headings) and Wix Madefor Text (body) via Google Fonts:
```html
<link href="https://fonts.googleapis.com/css2?family=Wix+Madefor+Display:wght@400;700;800&family=Wix+Madefor+Text:wght@400;500;700&display=swap" rel="stylesheet">
```

### Content block types (use inline styles — no <style> blocks)
- block-read:        white card, dark text
- block-think:       orange/yellow gradient
- block-fact:        blue gradient
- block-achievement: gold gradient

### Canvas HTML rules
- ALL styles must be fully inline — no `<style>` blocks, no external CSS
- No `<script>` tags in Canvas reading pages (JS lives in activity.html on GitHub)
- Activity pages CAN use JavaScript freely (they're served from GitHub Pages)

---

## Content standards

This is a **6th grade** course. Write for ages 11-12:
- Short paragraphs, active voice, relatable examples
- Avoid jargon unless you're defining it
- Interactive activities should be engaging and game-like where possible
- Quizzes: 5 questions, 1 point each, 3 attempts, per-answer feedback

---

## QTI 1.2 Quiz format

Quizzes export as QTI 1.2 zip files compatible with Canvas.
Each quiz: 5 questions, multiple choice, 1 point each, 3 attempts allowed.
Always include an answer key as a comment at the bottom of the source file.

---

## After building each lesson, confirm:

- [ ] `unit-N/lesson-N-M/reading.html` created
- [ ] `unit-N/lesson-N-M/activity.html` created  
- [ ] `unit-N/lesson-N-M/quiz.qti.zip` created
- [ ] `course-config.json` updated with this lesson's block
- [ ] File paths in config match actual file locations exactly

---

## Deploy reminder (for Ace, not Claude Code)

Once lessons are built and config is updated:
```bash
python canvas_deploy.py --dry-run     # preview first
python canvas_deploy.py --unit unit-1  # then deploy
```
