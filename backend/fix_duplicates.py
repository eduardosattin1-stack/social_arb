import psycopg2

conn = psycopg2.connect("postgresql://postgres:$ccp1985RDXz@db.otttlvrsgenixrxgzbcu.supabase.co:5432/postgres")
cur = conn.cursor()

# Check duplicate tickers
cur.execute("""
    SELECT entity_id, ticker, COUNT(*) as cnt
    FROM entity_tickers
    GROUP BY entity_id, ticker
    HAVING COUNT(*) > 1
""")
dups = cur.fetchall()
print(f"Duplicate ticker rows: {len(dups)}")

# Remove duplicates - keep only the first one
cur.execute("""
    DELETE FROM entity_tickers
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM entity_tickers
        GROUP BY entity_id, ticker
    )
""")
print(f"Deleted {cur.rowcount} duplicate ticker rows")

conn.commit()
conn.close()
print("Done!")
