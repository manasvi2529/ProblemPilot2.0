import sqlite3

conn = sqlite3.connect(r"data/problem2project.db")
c = conn.cursor()

admin = c.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1").fetchone()[0]
c.execute("UPDATE audit_logs SET user_id = ? WHERE user_id NOT IN (SELECT id FROM users)", (admin,))
conn.commit()

violations = c.execute("PRAGMA foreign_key_check").fetchall()
print(f"Foreign key violations remaining: {len(violations)}")
conn.close()
