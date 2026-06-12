import os
os.environ["DATABASE_URL"] = "postgresql://postgres:$ccp1985RDXz@db.otttlvrsgenixrxgzbcu.supabase.co:5432/postgres"

from source_runner import run_all_sources
from ai_pipeline import process_unprocessed_posts
from entity_pipeline import process_entity_mentions
from metrics_aggregator import aggregate_hourly_metrics
from entity_graph import seed_entity_graph
from signal_generator import generate_signals

print("=== Running full pipeline on Supabase ===")

print("\n1. Seeding entities...")
seed_entity_graph()

print("\n2. Ingesting sources...")
run_all_sources()

print("\n3. Running AI pipeline...")
process_unprocessed_posts()

print("\n4. Extracting entity mentions...")
process_entity_mentions()

print("\n5. Aggregating metrics...")
aggregate_hourly_metrics()

print("\n6. Generating signals...")
signals = generate_signals()

print(f"\n=== Done! Generated {len(signals)} signals ===")
for s in signals:
    print(f"  [{s['direction'].upper()}] {s['entity']} ({s['tickers']}): score={s['score']}")
