import requests
import os
import praw
from dotenv import load_dotenv

load_dotenv()

# Load API keys from .env
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Initialize Reddit
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

def fetch_wikipedia_intro(topic):
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.replace(' ', '_')}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("extract", "No summary available.")
        else:
            return f"No Wikipedia entry found for '{topic}'."
    except Exception as e:
        return f"[Wikipedia Error] {str(e)}"

def fetch_brave_articles(topic):
    try:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        params = {
            "q": topic,
            "count": 3
        }
        response = requests.get(url, headers=headers, params=params)
        results = response.json().get("web", {}).get("results", [])

        if not results:
            return "No Brave Search results found."

        summaries = []
        for result in results:
            summaries.append(f"Title: {result['title']}\nSnippet: {result['description']}\nURL: {result['url']}")

        return "\n\n".join(summaries)
    except Exception as e:
        return f"[Brave Search Error] {str(e)}"

def fetch_reddit_summary(topic, limit=3):
    try:
        posts = reddit.subreddit("all").search(topic, limit=limit, sort="relevance")
        summaries = []
        for post in posts:
            if not post.stickied:
                summaries.append(f"Title: {post.title}\nUpvotes: {post.score}\nComments: {post.num_comments}")
        return "\n\n".join(summaries)
    except Exception as e:
        return f"[Reddit Error] {str(e)}"

def gather_context(topic):
    wiki = fetch_wikipedia_intro(topic)
    brave = fetch_brave_articles(topic)
    reddit = fetch_reddit_summary(topic)

    return f"""📚 Wikipedia:
{wiki}

📰 Brave Search:
{brave}

🔥 Reddit Posts:
{reddit}
"""
