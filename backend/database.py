import psycopg2
from psycopg2.extras import RealDictCursor
from config import DATABASE_URL


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    conn.autocommit = True
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            source TEXT NOT NULL,
            post_id TEXT UNIQUE NOT NULL,
            content TEXT NOT NULL,
            author TEXT,
            timestamp TIMESTAMPTZ,
            region TEXT,
            sentiment REAL,
            topic TEXT,
            url TEXT,
            score INTEGER DEFAULT 0,
            num_comments INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_source ON posts(source)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_region ON posts(region)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_topic ON posts(topic)')
    conn.close()


if __name__ == "__main__":
    init_db()
    print("PostgreSQL database initialized.")
