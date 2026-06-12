import psycopg2
import yaml

DB_URL = "postgresql://postgres:$ccp1985RDXz@db.otttlvrsgenixrxgzbcu.supabase.co:5432/postgres"
conn = psycopg2.connect(DB_URL)
cur = conn.cursor()

with open("data/entity_seed.yaml") as f:
    data = yaml.safe_load(f)

count = 0
for ent in data.get("entities", []):
    try:
        cur.execute(
            "INSERT INTO entities (name, type, aliases) VALUES (%s, %s, %s) ON CONFLICT (name) DO NOTHING RETURNING id",
            (ent["name"], ent["type"], ",".join(ent.get("aliases", []))),
        )
        result = cur.fetchone()
        if result:
            eid = result[0]
        else:
            cur.execute("SELECT id FROM entities WHERE name = %s", (ent["name"],))
            eid = cur.fetchone()[0]
        if ent.get("ticker"):
            cur.execute(
                "INSERT INTO entity_tickers (entity_id, ticker, exchange, mcap_usd, mono_brand) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (eid, ent["ticker"], ent.get("exchange", ""), ent.get("mcap_usd", 0), ent.get("mono_brand", False)),
            )
        count += 1
    except Exception as e:
        print(f"Error: {e}")

conn.commit()
conn.close()
print(f"Seeded {count} entities to Supabase")
