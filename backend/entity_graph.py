import yaml
from pathlib import Path
from database import get_db_connection

SEED_PATH = Path(__file__).parent / "data" / "entity_seed.yaml"


def load_seed_entities() -> list[dict]:
    with open(SEED_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("entities", [])


def seed_entity_graph():
    entities = load_seed_entities()
    conn = get_db_connection()
    cursor = conn.cursor()

    for ent in entities:
        try:
            cursor.execute('''
                INSERT INTO entities (name, type, aliases)
                VALUES (%s, %s, %s)
                ON CONFLICT (name) DO NOTHING
                RETURNING id
            ''', (ent["name"], ent["type"], ",".join(ent.get("aliases", []))))

            result = cursor.fetchone()
            if result:
                entity_id = result["id"]
            else:
                cursor.execute("SELECT id FROM entities WHERE name = %s", (ent["name"],))
                entity_id = cursor.fetchone()["id"]

            if ent.get("ticker"):
                cursor.execute('''
                    INSERT INTO entity_tickers (entity_id, ticker, exchange, mcap_usd, mono_brand)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                ''', (
                    entity_id,
                    ent["ticker"],
                    ent.get("exchange", ""),
                    ent.get("mcap_usd", 0),
                    ent.get("mono_brand", False),
                ))
        except Exception as e:
            print(f"Error seeding {ent['name']}: {e}")

    conn.close()
    print(f"Seeded {len(entities)} entities.")


def build_alias_lookup() -> dict[str, int]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, aliases FROM entities")
    lookup = {}
    for row in cursor.fetchall():
        lookup[row["name"].lower()] = row["id"]
        if row["aliases"]:
            for alias in row["aliases"].split(","):
                alias = alias.strip().lower()
                if alias:
                    lookup[alias] = row["id"]
    conn.close()
    return lookup


def resolve_entities(text: str, alias_lookup: dict[str, int]) -> list[tuple[int, str]]:
    text_lower = text.lower()
    matches = []
    for alias, entity_id in sorted(alias_lookup.items(), key=lambda x: -len(x[0])):
        if alias in text_lower:
            matches.append((entity_id, alias))
    seen = set()
    unique = []
    for eid, alias in matches:
        if eid not in seen:
            seen.add(eid)
            unique.append((eid, alias))
    return unique[:5]


if __name__ == "__main__":
    seed_entity_graph()
