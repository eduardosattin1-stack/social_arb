import sqlite3

def analyze_trends():
    conn = sqlite3.connect("social_radar.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get top 15 tech trends from HackerNews
    cursor.execute("SELECT content, sentiment, region FROM posts WHERE source = 'HackerNews' ORDER BY timestamp DESC LIMIT 15")
    hn_posts = cursor.fetchall()
    
    # Get mocked twitter data
    cursor.execute("SELECT content, sentiment, region FROM posts WHERE source = 'Twitter' ORDER BY timestamp DESC LIMIT 5")
    twitter_posts = cursor.fetchall()
    
    conn.close()
    
    print("=== TRENDING IN TECH (HackerNews) ===")
    for idx, row in enumerate(hn_posts):
        print(f"{idx+1}. [{row['region']}] (Sentiment: {row['sentiment']}) - {row['content']}")
        
    print("\n=== TRENDING IN SOCIAL (Twitter Mock) ===")
    for idx, row in enumerate(twitter_posts):
        print(f"{idx+1}. [{row['region']}] (Sentiment: {row['sentiment']}) - {row['content']}")

if __name__ == "__main__":
    analyze_trends()
