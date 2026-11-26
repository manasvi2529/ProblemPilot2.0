import sqlite3

conn = sqlite3.connect(r"data/problem2project.db")
c = conn.cursor()

admin = c.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1").fetchone()[0]
print("Using admin owner ID:", admin)

orphans = c.execute("""
    SELECT r.id, r.session_id, r.title, r.created_at, r.owner_id
    FROM research_reports r
    LEFT JOIN research_sessions s ON r.session_id = s.id
    WHERE s.id IS NULL
""").fetchall()

distinct_sessions = {}
for r in orphans:
    s_id = r[1]
    if s_id and s_id not in distinct_sessions:
        distinct_sessions[s_id] = (r[2], r[3], r[4] or admin)

for s_id, (title, dt, owner_id) in distinct_sessions.items():
    c.execute("""
        INSERT INTO research_sessions (
            id, owner_id, query, domain, target_users, geography, constraints,
            status, used_live_search, progress_pct, current_step, step_message,
            created_at, completed_at
        )
        VALUES (?, ?, ?, 'General', 'General Users', 'Global', 'None', 'completed', 0, 100, 'completed', 'Archived historical research session', ?, ?)
    """, (s_id, owner_id, title or "Historical Research", dt, dt))

conn.commit()

violations_after = c.execute("PRAGMA foreign_key_check").fetchall()
print(f"Repaired {len(distinct_sessions)} parent sessions.")
print(f"Foreign key violations remaining: {len(violations_after)}")
conn.close()
