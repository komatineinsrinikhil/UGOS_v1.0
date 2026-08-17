"""
Extracts the JSON schemas embedded in the UGOS specification documents into
schemas/v1/<module>/<name>.json, so the schemas the specs describe exist as
files rather than only as fenced blocks inside prose.

Run from anywhere:

    python extract_schemas.py
"""

import json
import re
import sys
from pathlib import Path

# Resolve relative to this file, not to whoever's machine wrote it. The
# previous version hardcoded an absolute Windows path, so the script could
# only ever run on one computer -- which is why schemas/v1 stayed empty.
ROOT_DIR = Path(__file__).resolve().parent
SCHEMAS_OUT_DIR = ROOT_DIR / "schemas" / "v1"

SKIP_DIRS = {"schemas", ".git", ".venv", "node_modules", "__pycache__", "archive"}


def sanitize_filename(name: str) -> str:
    """Creates a clean snake_case filename."""
    clean = re.sub(r"[^\w\s-]", "", str(name)).strip().lower()
    return re.sub(r"[-\s]+", "_", clean) or "schema"


def extract_schemas() -> int:
    print("=" * 65)
    print("UGOS -- extracting JSON schemas from the specification")
    print("=" * 65)

    SCHEMAS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    extracted = skipped = scanned = 0
    invalid = []

    pattern = re.compile(r"```\s*json\s*[\r\n]+([\s\S]*?)```", re.IGNORECASE)

    for md_file in sorted(ROOT_DIR.rglob("*.md")):
        if SKIP_DIRS & set(md_file.parts):
            continue

        scanned += 1
        try:
            content = md_file.read_text(encoding="utf-8-sig")
        except Exception:
            content = md_file.read_text(encoding="utf-8", errors="ignore")

        matches = pattern.findall(content)
        if not matches:
            continue

        module_folder = md_file.parent.name
        output_folder = SCHEMAS_OUT_DIR / module_folder

        for idx, block in enumerate(matches, start=1):
            block_clean = block.strip()
            if not block_clean:
                continue

            try:
                parsed = json.loads(block_clean)
            except json.JSONDecodeError as exc:
                # Illustrative snippets are not all valid JSON. Recorded rather
                # than printed one by one, so a real problem stays visible.
                invalid.append(f"{md_file.name} #{idx}: {exc}")
                skipped += 1
                continue

            output_folder.mkdir(parents=True, exist_ok=True)

            title = ""
            if isinstance(parsed, dict):
                title = (
                    parsed.get("title")
                    or parsed.get("name")
                    or parsed.get("workflow_id")
                    or parsed.get("agent_id")
                    or parsed.get("event_type")
                    or parsed.get("routing_id")
                    or parsed.get("task_id")
                    or (parsed.get("$id", "").split("/")[-1].replace(".json", "")
                        if parsed.get("$id") else "")
                )
            if not title:
                title = f"{md_file.stem}_schema_{idx}"

            out_path = output_folder / f"{sanitize_filename(title)}.json"
            # Two blocks in one document can share a title; do not silently
            # overwrite one with the other.
            n = 2
            while out_path.exists():
                out_path = output_folder / f"{sanitize_filename(title)}_{n}.json"
                n += 1

            out_path.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
            print(f"  [+] {module_folder}/{out_path.name}")
            extracted += 1

    print("-" * 65)
    print(f"  Documents scanned : {scanned}")
    print(f"  Schemas written   : {extracted}")
    print(f"  Blocks skipped    : {skipped} (not valid JSON on their own)")
    print(f"  Destination       : {SCHEMAS_OUT_DIR.relative_to(ROOT_DIR)}")
    if invalid:
        print("\n  Skipped blocks:")
        for line in invalid[:10]:
            print(f"    - {line}")
        if len(invalid) > 10:
            print(f"    ... and {len(invalid) - 10} more")
    print("=" * 65)
    return extracted


if __name__ == "__main__":
    sys.exit(0 if extract_schemas() else 1)
