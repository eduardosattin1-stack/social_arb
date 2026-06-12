import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/social_radar"
)

NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "SocialRadar/1.0")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

LLM_DAILY_TOKEN_BUDGET = int(os.getenv("LLM_DAILY_TOKEN_BUDGET", "50000"))
