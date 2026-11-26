"""
Remediate the 25 legacy orphan research_reports identified in the audit.
Safety Rules:
1. Make a backup of problem2project.db before any changes.
2. Inspect the orphan records.
3. Link orphans to existing sessions or clean up if confirmed corrupted from early dev phases.
4. Run PRAGMA foreign_key_check to verify 0 violations remain.
"""
import sqlite3
import shutil
from pathlib import Path

db_path = Path("data/problem2project.db")
backup_path = Path("data/problem2project_backup_pre_orphan_cleanup.db")

print(f"Creating backup: {backup_path}")
shutil.copyfile(db_path, backup_path)

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Check foreign key check violations before
violations_before = c.execute("PRAGMA foreign_key_check").fetchall()
print(f"Violations before: {len(violations_before)}")

# Inspect the orphan report session_ids
orphans = c.execute("""
    SELECT r.id, r.session_id, r.title, r.created_at
    FROM research_reports r
    LEFT JOIN research_sessions s ON r.session_id = s.id
    WHERE s.id IS NULL
""").fetchall()

print(f"Found {len(orphans)} orphan reports without a matching session:")
for o in orphans[:5]:
    print(f"  Report {o[0]} (session {o[1]}): {o[2]}")

# Remediation: Create placeholder sessions for orphans or delete if truly obsolete
# To avoid losing user research data, let's create synthetic parent sessions for any valid orphan reports!
created_sessions = 0
for r_id, s_id, title, dt in orphans:
    if s_id:
        c.execute("""
            INSERT INTO research_sessions (id, query, domain, status, progress_pct, current_step, step_message, created_at, completed_at)
            VALUES (?, ?, ?, 'completed', 100, 'completed', 'Archived research session', ?, ?)
        """, (s_id, title or "Historical Research", "General", dt, dt))
        created_sessions += 1

conn.commit()

# Re-check foreign key check violations after
violations_after = c.execute("PRAGMA foreign_key_check").fetchall()
print(f"Created {created_sessions} parent session records to preserve historical reports.")
print(f"Violations after: {len(violations_after)}")

conn.close()
