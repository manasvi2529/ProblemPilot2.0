import sqlite3

conn = sqlite3.connect(r"data/problem2project.db")
c = conn.cursor()

fk_checks = c.execute("PRAGMA foreign_key_check").fetchall()
print("Foreign key check violations:", len(fk_checks))

target_id = "47667aa6-cf44-4d09-b5a7-d2d9bb239d05"
proj = c.execute("SELECT id, owner_id, name, status, current_stage FROM projects WHERE id = ?", (target_id,)).fetchone()
print("Target Project:", proj)

files = c.execute("SELECT COUNT(*) FROM project_files WHERE project_id = ?", (target_id,)).fetchone()[0]
print("Target Project Files count:", files)

admins = c.execute("SELECT id, username, email, role, tier, is_active FROM users WHERE role = 'admin'").fetchall()
print("Admin accounts:", admins)

# Check total counts across core tables
for t in ["users", "projects", "project_files", "research_sessions", "research_reports", "quota_policies", "user_usages", "token_blacklists"]:
    cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"Table {t}: {cnt}")

conn.close()
