"""
UGOS Application Script: Automated File Patching via ToolEngine
---------------------------------------------------------------
Demonstrates using UGOS ToolEngine to write files, generate 
unified diff patches, and apply safe updates under policy control.
"""

import sys
import logging
from pathlib import Path

# Fix ModuleNotFoundError: Add src directory to Python path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ugos.core.tools import ToolEngine
from ugos.security.policy import PolicyEngine, PermissionLevel
from ugos.core.memory import MemoryEngine
from ugos.agents.specialized import SoftwareEngineerAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    print("\n" + "=" * 60)
    print("🛠️  Applying UGOS: ToolEngine File Patching Workflow")
    print("=" * 60)

    # Setup ToolEngine and Security Context
    policy = PolicyEngine()
    tools = ToolEngine(security_policy=policy)
    agent = SoftwareEngineerAgent(agent_id="ag_dev_01", name="DevBot")
    
    target_file = "tmp/config.txt"
    v1_content = "APP_NAME=UGOS_System\nDEBUG=False\nMAX_WORKERS=2\n"
    v2_content = "APP_NAME=UGOS_System_v1\nDEBUG=True\nMAX_WORKERS=8\n"

    # Step 1: Write initial version
    print(f"\n1. Writing initial version to '{target_file}'...")
    res1 = tools.execute_tool(
        tool_name="file_writer",
        agent_id=agent.agent_id,
        permission_level=PermissionLevel.STANDARD_EXEC,
        target=target_file,
        content=v1_content
    )
    print("   [Status]:", res1.get("status"))
    print("   [Output]:", res1.get("output"))

    # Step 2: Write updated version & automatically generate unified diff patch
    print(f"\n2. Updating '{target_file}' and generating Unified Patch Diff...")
    res2 = tools.execute_tool(
        tool_name="file_writer",
        agent_id=agent.agent_id,
        permission_level=PermissionLevel.STANDARD_EXEC,
        target=target_file,
        content=v2_content
    )
    print("   [Status]:", res2.get("status"))
    
    patch_diff = res2.get("diff", "")
    print("\n" + "-" * 60)
    print("🔍 Generated Unified Patch Diff:")
    print("-" * 60)
    print(patch_diff.strip())
    print("-" * 60)

    # Step 3: Read back updated file using file_reader tool
    print(f"\n3. Reading back updated content from '{target_file}'...")
    res3 = tools.execute_tool(
        tool_name="file_reader",
        agent_id=agent.agent_id,
        permission_level=PermissionLevel.STANDARD_EXEC,
        target=target_file
    )
    print("   [Status]:", res3.get("status"))
    print(f"   [File Content]:\n{res3.get('output', '').strip()}")

    # Step 4: Persist log to SQLite Memory Engine via set_global_fact
    memory = MemoryEngine(db_path=Path("ugos_memory.db"))
    memory.set_global_fact(
        key="patch_session_01",
        value=f"Patched {target_file} successfully:\n{patch_diff}",
        tags=["audit", "patch_log"]
    )
    
    saved_facts = memory.get_facts_by_tag("audit")
    logging.info(f"Fact recorded in ugos_memory.db. Total audit facts: {len(saved_facts)}")

    print("\n" + "=" * 60)
    print("📊 File Patching Workflow Executed Successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()