from sqlalchemy import (
    Table, Column, Integer, String, Text, Float, DateTime, Boolean,
    ForeignKey, Index, MetaData, Enum as SAEnum
)
from sqlalchemy.sql import func

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

posts = Table(
    "posts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String, nullable=False),
    Column("post_id", String, unique=True, nullable=False),
    Column("content", Text, nullable=False),
    Column("author", String),
    Column("timestamp", DateTime(timezone=True)),
    Column("region", String),
    Column("sentiment", Float),
    Column("topic", String),
    Column("url", Text),
    Column("score", Integer, default=0),
    Column("num_comments", Integer, default=0),
    Column("lang", String(10)),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Index("idx_posts_source", "source"),
    Index("idx_posts_timestamp", "timestamp"),
    Index("idx_posts_region", "region"),
    Index("idx_posts_topic", "topic"),
    Index("idx_posts_lang", "lang"),
)

entities = Table(
    "entities",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False, unique=True),
    Column("type", String(20), nullable=False),
    Column("aliases", Text),
    Column("lang_aliases", Text),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

entity_links = Table(
    "entity_links",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("child_id", Integer, ForeignKey("entities.id"), nullable=False),
    Column("parent_id", Integer, ForeignKey("entities.id"), nullable=False),
    Column("relation", String(20), nullable=False),
)

entity_tickers = Table(
    "entity_tickers",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("entity_id", Integer, ForeignKey("entities.id"), nullable=False),
    Column("ticker", String(10), nullable=False),
    Column("exchange", String(10)),
    Column("mcap_usd", Float),
    Column("revenue_share_est", Float),
    Column("mono_brand", Boolean, default=False),
    Column("updated_at", DateTime(timezone=True), server_default=func.now()),
    Index("idx_entity_tickers_ticker", "ticker"),
)

entity_mentions = Table(
    "entity_mentions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("post_id", Integer, ForeignKey("posts.id"), nullable=False),
    Column("entity_id", Integer, ForeignKey("entities.id"), nullable=False),
    Column("matched_text", String),
    Column("method", String(20)),
    Column("intent", String(30)),
    Column("intent_score", Float),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Index("idx_entity_mentions_entity", "entity_id", "created_at"),
)

entity_metrics_hourly = Table(
    "entity_metrics_hourly",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("entity_id", Integer, ForeignKey("entities.id"), nullable=False),
    Column("ts_hour", DateTime(timezone=True), nullable=False),
    Column("platform", String(30)),
    Column("region", String(20)),
    Column("mention_count", Integer, default=0),
    Column("weighted_mentions", Float, default=0),
    Column("sentiment_mean", Float),
    Column("sentiment_std", Float),
    Column("intent_purchase_share", Float),
    Column("intent_churn_share", Float),
    Column("scarcity_share", Float),
    Column("unique_authors", Integer, default=0),
    Column("computed_at", DateTime(timezone=True), server_default=func.now()),
    Index("idx_entity_metrics_hourly", "entity_id", "ts_hour"),
)

signals = Table(
    "signals",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("entity_id", Integer, ForeignKey("entities.id"), nullable=False),
    Column("tickers", Text),
    Column("direction", String(10), nullable=False),
    Column("signal_score", Float),
    Column("gap_score", Float),
    Column("demand_index", Float),
    Column("awareness_index", Float),
    Column("velocity_z", Float),
    Column("acceleration", Float),
    Column("corroboration", Integer),
    Column("intent_purchase_share", Float),
    Column("materiality", Float),
    Column("regions", Text),
    Column("origin_platform", String(30)),
    Column("novelty", Boolean, default=False),
    Column("evidence_post_ids", Text),
    Column("narrative", Text),
    Column("status", String(20), default="new"),
)

verdicts = Table(
    "verdicts",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("signal_id", Integer, ForeignKey("signals.id"), nullable=False),
    Column("verdict", String(20), nullable=False),
    Column("note", Text),
    Column("at", DateTime(timezone=True), server_default=func.now()),
)

resolution_cache = Table(
    "resolution_cache",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("query_text", String, nullable=False, unique=True),
    Column("entity_name", String),
    Column("entity_type", String(20)),
    Column("parent_company", String),
    Column("ticker", String(10)),
    Column("exchange", String(10)),
    Column("mono_brand", Boolean),
    Column("confidence", Float),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)
