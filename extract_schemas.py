import os
import re
import json
from pathlib import Path

# Base Paths
ROOT_DIR = Path(r"C:\Users\lenovo\UGOS_v1.0_SPECIFICATION")
SCHEMAS_OUT_DIR = ROOT_DIR / "schemas" / "v1"

def sanitize_filename(name: str) -> str:
    """Creates a clean snake_case filename."""
    clean = re.sub(r"[^\w\s-]", "", name).strip().lower()
    return re.sub(r"[-\s]+", "_", clean)

def extract_schemas():
    print("=" * 65)
    print("🚀 MILESTONE 1: EXTRACTING JSON SCHEMAS (BOM-SAFE)")
    print("=" * 65)

    SCHEMAS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    extracted_count = 0
    file_count = 0

    # Pattern targeting json code blocks
    pattern = re.compile(r"```\s*json\s*[\r\n]+([\s\S]*?)```", re.IGNORECASE)

    for md_file in ROOT_DIR.rglob("*.md"):
        if "schemas" in md_file.parts:
            continue
            
        file_count += 1
        
        # utf-8-sig strips hidden Windows UTF-8 BOM headers (\ufeff)
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
                output_folder.mkdir(parents=True, exist_ok=True)

                # Derive filename from schema metadata
                schema_title = ""
                if isinstance(parsed, dict):
                    schema_title = (
                        parsed.get("title") 
                        or parsed.get("name")
                        or parsed.get("workflow_id")
                        or parsed.get("agent_id")
                        or parsed.get("event_type")
                        or (parsed.get("$id", "").split("/")[-1].replace(".json", "") if parsed.get("$id") else None)
                    )
                
                if not schema_title:
                    schema_title = f"{md_file.stem}_schema_{idx}"
                
                filename = f"{sanitize_filename(schema_title)}.json"
                out_path = output_folder / filename

                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(parsed, f, indent=2)

                print(f"  [+] Saved: {module_folder}/{filename}")
                extracted_count += 1

            except json.JSONDecodeError as e:
                print(f"  [!] Invalid JSON in {md_file.name} (#{idx}): {e}")

    print("-" * 65)
    print(f"✅ EXTRACTION COMPLETE")
    print(f"  • Documents Scanned : {file_count}")
    print(f"  • Schemas Saved     : {extracted_count}")
    print(f"  • Destination       : {SCHEMAS_OUT_DIR}")
    print("=" * 65)

if __name__ == "__main__":
    extract_schemas()