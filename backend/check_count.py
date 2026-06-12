import psycopg2
conn = psycopg2.connect("postgresql://postgres:$ccp1985RDXz@db.otttlvrsgenixrxgzbcu.supabase.co:5432/postgres")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM entities")
print(f"Total entities: {cur.fetchone()[0]}")
cur.execute("SELECT name FROM entities ORDER BY id DESC LIMIT 20")
print("\nLast 20 entities:")
for r in cur.fetchall():
    print(f"  {r[0]}")
conn.close()
