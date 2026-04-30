#!/usr/bin/env python3
"""Canvas deploy script for OAO Digital Discoveries.

Reads course-config.json, creates Canvas Modules per Unit, and populates each
week with Pages (iframe-embed to GitHub Pages) and Quizzes (QTI 1.2 import).

Usage:
  python canvas_deploy.py --dry-run             # preview, no API writes
  python canvas_deploy.py --unit unit-1         # deploy a single unit
  python canvas_deploy.py --unit unit-1 --week 3   # deploy a single week
  python canvas_deploy.py --all                 # deploy everything

Auth: token is read from CANVAS_API_TOKEN env var first, then from
course-config.json (canvas_api_token field). The config file is gitignored.

Idempotency: if a Module with the same name already exists, this script reuses
it but will add duplicate items on each run. To redeploy cleanly, delete the
Module in Canvas first, then rerun.

Requires: pip install requests
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: pip install requests")


CONFIG_PATH = Path("course-config.json")


def load_config():
    if not CONFIG_PATH.exists():
        sys.exit(f"Missing {CONFIG_PATH} — copy course-config.example.json to course-config.json")
    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    token = os.environ.get("CANVAS_API_TOKEN") or cfg["course"].get("canvas_api_token", "")
    if not token or token.startswith(("REPLACE", "ROTATE")):
        sys.exit(
            "ERROR: No Canvas API token. Set CANVAS_API_TOKEN env var, "
            "or paste a valid token into course-config.json (canvas_api_token)."
        )
    cfg["_token"] = token
    return cfg


class CanvasClient:
    def __init__(self, base_url, token, course_id, dry_run=False, verbose=True):
        self.base = f"{base_url.rstrip('/')}/api/v1/courses/{course_id}"
        self.headers = {"Authorization": f"Bearer {token}"}
        self.dry_run = dry_run
        self.verbose = verbose

    def _request(self, method, path, **kwargs):
        url = path if path.startswith("http") else f"{self.base}{path}"
        if self.dry_run and method.upper() != "GET":
            if self.verbose:
                print(f"      [DRY] {method} {url}")
            return {}
        r = requests.request(method, url, headers=self.headers, timeout=60, **kwargs)
        if not r.ok:
            print(f"      HTTP {r.status_code} on {method} {url}")
            print(f"      Response: {r.text[:400]}")
            r.raise_for_status()
        return r.json() if r.content else {}

    def list_modules(self):
        return self._request("GET", "/modules", params={"per_page": 100}) or []

    def list_quizzes(self):
        return self._request("GET", "/quizzes", params={"per_page": 100}) or []

    def find_module_by_name(self, name):
        for m in self.list_modules():
            if m.get("name") == name:
                return m
        return None

    def create_module(self, name, position):
        return self._request(
            "POST", "/modules", json={"module": {"name": name, "position": position}}
        )

    def find_or_create_module(self, name, position):
        existing = self.find_module_by_name(name)
        if existing:
            print(f"      (reusing existing module #{existing.get('id')})")
            return existing
        return self.create_module(name, position)

    def update_module(self, module_id, **fields):
        return self._request("PUT", f"/modules/{module_id}", json={"module": fields})

    def create_page(self, title, body):
        return self._request(
            "POST",
            "/pages",
            json={"wiki_page": {"title": title, "body": body, "published": True}},
        )

    def add_module_item(self, module_id, item):
        return self._request(
            "POST", f"/modules/{module_id}/items", json={"module_item": item}
        )

    def add_subheader(self, module_id, title):
        return self.add_module_item(module_id, {"type": "SubHeader", "title": title})

    def import_qti(self, zip_path):
        """Import a QTI 1.2 zip and return the resulting quiz dict (or None in dry-run)."""
        if self.dry_run:
            print(f"      [DRY] would import QTI: {zip_path}")
            return None

        existing_quiz_ids = {q["id"] for q in self.list_quizzes()}

        zip_path = Path(zip_path)
        file_size = zip_path.stat().st_size

        # Step 1: register the migration with pre_attachment
        mig = self._request(
            "POST",
            "/content_migrations",
            json={
                "migration_type": "qti_converter",
                "pre_attachment": {"name": zip_path.name, "size": file_size},
            },
        )
        # Step 2: upload to the file URL Canvas gives us
        upload_url = mig["pre_attachment"]["upload_url"]
        upload_params = mig["pre_attachment"].get("upload_params", {})
        with zip_path.open("rb") as f:
            files = {"file": (zip_path.name, f, "application/zip")}
            up = requests.post(upload_url, data=upload_params, files=files, timeout=120)
            if not up.ok:
                raise RuntimeError(f"Upload failed: {up.status_code} {up.text[:200]}")

        # Step 3: poll for completion
        mig_id = mig["id"]
        for _ in range(60):  # up to ~5 minutes
            status = self._request("GET", f"/content_migrations/{mig_id}")
            state = status.get("workflow_state")
            if state == "completed":
                # Find which quiz was newly created
                new_quizzes = [q for q in self.list_quizzes() if q["id"] not in existing_quiz_ids]
                if new_quizzes:
                    return new_quizzes[0]
                print("      WARN: migration completed but no new quiz detected")
                return None
            if state == "failed":
                raise RuntimeError(f"QTI import failed: {status.get('migration_issues_url')}")
            time.sleep(5)
        raise RuntimeError("QTI import timed out (>5 min)")


def build_iframe_html(github_url, title):
    """Canvas Page body that iframes a GitHub-Pages-hosted reading or activity."""
    return (
        f'<p><iframe src="{github_url}" width="100%" height="1100" '
        f'frameborder="0" allow="fullscreen" allowfullscreen "scrolling="auto" '
        f'title="{title}" style="border:0;"></iframe></p>\n'
        f'<p style="font-size:12px;color:#666;margin-top:8px;">'
        f'If the content above does not load, '
        f'<a href="{github_url}" target="_blank" rel="noopener">open it in a new tab</a>.</p>'
    )


def deploy_unit(client, unit, github_base, week_filter=None):
    module_name = unit["title"]
    print(f"\n=== {module_name} ===")
    module = client.find_or_create_module(module_name, unit["canvas_module_position"])
    module_id = module.get("id")

    weeks = unit["weeks"]
    if week_filter is not None:
        weeks = [w for w in weeks if w["week_number"] == week_filter]
        if not weeks:
            print(f"  No week {week_filter} in {unit['id']}")
            return

    for week in weeks:
        print(f"\n  Week {week['week_number']}: {week['title']}")
        client.add_subheader(module_id, week["title"])

        for item in week["items"]:
            title = item["title"]
            file_path = Path(item["file"])
            print(f"    + {title}")

            if not file_path.exists():
                print(f"      ! WARNING: file not found, skipping: {file_path}")
                continue

            # Translate human-readable config types to Canvas API types.
            # Canvas API valid types: must_view, must_contribute, must_submit, min_score, must_mark_done
            cr_type_map = {"must_score_at_least": "min_score"}
            raw_cr = item.get("completion_requirement", "must_view")
            api_cr_type = cr_type_map.get(raw_cr, raw_cr)
            cr = {"type": api_cr_type}
            if api_cr_type == "min_score":
                cr["min_score"] = item.get("min_score", 0)

            if item["type"] == "page":
                gh_url = f"{github_base.rstrip('/')}/{file_path.as_posix()}"
                body = build_iframe_html(gh_url, title)
                page = client.create_page(title, body)
                if page:
                    client.add_module_item(
                        module_id,
                        {
                            "type": "Page",
                            "page_url": page["url"],
                            "title": title,
                            "completion_requirement": cr,
                        },
                    )

            elif item["type"] == "quiz":
                quiz = client.import_qti(file_path)
                if quiz:
                    client.add_module_item(
                        module_id,
                        {
                            "type": "Quiz",
                            "content_id": quiz["id"],
                            "title": title,
                            "completion_requirement": cr,
                        },
                    )
            else:
                print(f"      ! Unknown item type: {item['type']}")

    # Set prerequisite (unlock-after) — only after all units are placed
    if unit.get("unlock_after_unit"):
        prereq_unit_id = unit["unlock_after_unit"]
        # Look up the prerequisite module by matching its config-derived title.
        # We do a fuzzy match because we may not have created it in this run.
        # The cleanest approach: look up the unit's title from config (caller passes it).
        # For simplicity here, we rely on naming convention: "Unit N: ...".
        prereq_modules = [
            m for m in client.list_modules()
            if m.get("name", "").startswith(prereq_unit_id.replace("-", " ").title())
        ]
        if prereq_modules and not client.dry_run:
            client.update_module(
                module_id, prerequisite_module_ids=[prereq_modules[0]["id"]]
            )


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="Print actions without making API writes")
    p.add_argument("--unit", help="Deploy a single unit (e.g. unit-1)")
    p.add_argument("--week", type=int, help="Deploy a single week (use with --unit)")
    p.add_argument("--all", action="store_true", help="Deploy all units")
    args = p.parse_args()

    if not (args.unit or args.all or args.dry_run):
        p.error("Specify --dry-run, --unit, or --all")

    cfg = load_config()
    course = cfg["course"]
    print(f"Course: {course['name']} (Canvas course #{course['canvas_course_id']})")
    print(f"Canvas: {course['canvas_base_url']}")

    github_base = cfg.get("github_pages", {}).get("base_url") or course["github_pages_base_url"]
    print(f"GitHub Pages: {github_base}")

    if args.dry_run:
        print("Mode: DRY RUN (no API writes)")

    client = CanvasClient(
        course["canvas_base_url"],
        cfg["_token"],
        course["canvas_course_id"],
        dry_run=args.dry_run,
    )

    units = cfg["units"]
    if args.unit:
        units = [u for u in units if u["id"] == args.unit]
        if not units:
            sys.exit(f"Unit not found: {args.unit}")

    for unit in units:
        deploy_unit(client, unit, github_base, week_filter=args.week)

    print("\nDone." + (" (dry run — nothing changed in Canvas)" if args.dry_run else ""))


if __name__ == "__main__":
    main()
