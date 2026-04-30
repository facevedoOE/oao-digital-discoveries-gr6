# OAO Digital Discoveries — Grade 6

Course files for **6th Grade Digital Discoveries** (CPALMS Course #0200021), an asynchronous self-paced computer science course delivered through Canvas LMS for Optima Academy Online.

## Repo layout

```
.
├── Unit1/                            Weeks 1–8 (Digital Foundations)
│   ├── week-NN-reading.html          → Canvas Page (iframe to GitHub Pages)
│   ├── week-NN-activity.html         → Canvas Page (iframe to GitHub Pages)
│   ├── week-NN-quiz-canvas-import.zip → Canvas Quiz (QTI 1.2 import)
│   ├── week-NN-answer-key.txt        Manual answer key (fallback)
│   └── unit-1-assessment-canvas-import.zip  Unit 1 summative
├── Unit2/                            Weeks 9–18 (Data & Cyber Safety)
├── assets/
│   └── oao-logo.png                  Header logo (referenced by every reading)
├── course-config.json                Deploy config — GITIGNORED, contains API token
├── course-config.example.json        Sanitized template (committed)
├── canvas_deploy.py                  Push the course to Canvas via API
├── .gitignore
└── README.md
```

Reading and activity HTML pages are hosted on GitHub Pages and embedded in Canvas via iframes. Quizzes are imported as QTI 1.2 zip files.

## GitHub Pages URL

`https://facevedoOE.github.io/oao-digital-discoveries-gr6/`

To enable: Settings → Pages → Source: `main`, root.

## Deploying to Canvas

### One-time setup

1. **Rotate your Canvas API token** (the previous one was committed to git history). In Canvas: Account → Settings → New Access Token.
2. Save the new token via one of:
   - Set the `CANVAS_API_TOKEN` environment variable (preferred)
   - Or paste it into `course-config.json` under `course.canvas_api_token` (file is gitignored)
3. `pip install requests`
4. Push the latest content to `main` so GitHub Pages serves it.

### Deploy commands

```bash
# Preview without making changes
python canvas_deploy.py --dry-run --all

# Deploy a single unit
python canvas_deploy.py --unit unit-1

# Deploy a single week within a unit (for incremental updates)
python canvas_deploy.py --unit unit-2 --week 11

# Deploy everything
python canvas_deploy.py --all
```

### Idempotency caveat

If a Canvas Module with the same name already exists, the script reuses it but still adds new items each run, which can create duplicates. To redeploy a unit cleanly, delete the Canvas Module first, then run the deploy command.

## Building new lessons

For each new week, produce three files in the appropriate `UnitN/` folder:

1. `week-NN-reading.html` — Standalone HTML reading page (light theme, OAO design system, references `../assets/oao-logo.png`)
2. `week-NN-activity.html` — Vanilla-JS interactive (no external libs, scenario-based, XP scoring, postMessage to Canvas parent)
3. `week-NN-quiz-canvas-import.zip` — QTI 1.2 zip (5 questions, 1 pt each, 3 attempts) + `week-NN-answer-key.txt` fallback

Then add the week's entry to `course-config.json` under the right unit's `weeks` array. The deploy script reads this config to know what to push.

## Design system (quick reference)

Colors: Binary Blue `#0E1C42`, Bitstream Blue `#55C8E8`, Gateway Gold `#C7922C`, Portal Purple `#67308F`, Gamer Green `#76C043`, Odyssey Orange `#F78F1E`.

Fonts: Wix Madefor Display (headings) + Wix Madefor Text (body), via Google Fonts.

Reading-page template: `Unit1/week-01-reading.html` is the canonical reference.

## Standards covered

Florida Computer Science Standards (SC.6.*) — see `course-config.json` for per-week alignment.

## License & attribution

Internal Optima Academy Online course materials. Not for redistribution.
