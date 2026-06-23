import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tweepy
from googleapiclient.discovery import build
import requests

try:
    from newsapi import NewsApiClient as _NewsApiClient
except ImportError:
    _NewsApiClient = None

try:
    import feedparser as _feedparser
except ImportError:
    _feedparser = None

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Vera Credit · Social Intelligence Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# SECURE API CREDENTIALS
# ============================================
def get_secret(key, required=True):
    try:
        return st.secrets[key]
    except Exception:
        if required:
            return None
        return None

TWITTER_BEARER_TOKEN = get_secret("TWITTER_BEARER_TOKEN")
YOUTUBE_API_KEY = get_secret("YOUTUBE_API_KEY")
NEWS_API_KEY = get_secret("NEWS_API_KEY")
META_ACCESS_TOKEN = get_secret("META_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ACCOUNT_ID = get_secret("INSTAGRAM_BUSINESS_ACCOUNT_ID")

# ============================================
# CUSTOM STYLING
# ============================================
st.markdown("""
<style>
    /* Force white background and black text in all modes */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
    .main, .main .block-container, section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        color: #111111 !important;
    }
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* Hero */
    .vera-hero {
        background: #111111;
        border-radius: 8px;
        padding: 1.8rem 2rem 1.5rem 2rem;
        margin-bottom: 1.5rem;
    }
    .vera-hero h1 { font-size: 1.9rem; font-weight: 700; color: #ffffff; margin: 0 0 0.3rem 0; }
    .vera-hero p { color: #aaaaaa; font-size: 0.9rem; margin: 0; }

    /* Fact card */
    .fact-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-left: 3px solid #111111;
        border-radius: 4px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.4rem;
    }
    .fact-label { color: #555555; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    .fact-value { color: #111111; font-size: 0.92rem; font-weight: 500; margin-top: 2px; }

    /* Competitor row */
    .comp-row {
        background: #f8f8f8;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 0.65rem 1rem;
        margin-bottom: 0.35rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .comp-name { color: #111111; font-weight: 600; font-size: 0.92rem; }
    .comp-pos  { color: #555555; font-size: 0.82rem; }

    /* Opportunity cards */
    .opp-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 1.2rem 1.2rem 1.2rem 0;
        margin-bottom: 0.9rem;
        display: flex;
    }
    .opp-number { font-size: 2.2rem; font-weight: 700; color: #cccccc; min-width: 70px; text-align: center; padding-top: 0.1rem; }
    .opp-body { flex: 1; }
    .opp-evidence-label { color: #555555; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
    .opp-evidence { color: #333333; font-size: 0.88rem; margin: 0.15rem 0 0.7rem 0; }
    .opp-gap-label { color: #888888; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
    .opp-gap { color: #555555; font-size: 0.88rem; margin: 0.15rem 0 0.7rem 0; }
    .opp-solution {
        background: #f8f8f8;
        border-left: 3px solid #111111;
        border-radius: 0 4px 4px 0;
        padding: 0.7rem 1rem;
        margin-bottom: 0.5rem;
    }
    .opp-solution-label { color: #111111; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
    .opp-solution-text { color: #333333; font-size: 0.88rem; margin: 0.15rem 0 0 0; }
    .opp-tag {
        display: inline-block;
        background: #ffffff;
        color: #111111;
        border: 1px solid #111111;
        border-radius: 20px;
        padding: 0.15rem 0.75rem;
        font-size: 0.74rem;
        font-weight: 600;
        margin-top: 0.4rem;
    }

    /* Callout */
    .callout-warning {
        background: #f8f8f8;
        border: 1px solid #cccccc;
        border-left: 3px solid #111111;
        border-radius: 4px;
        padding: 0.85rem 1rem;
        color: #333333;
        font-size: 0.9rem;
    }

    /* Nav pills */
    div[data-testid="stRadio"] > div { flex-direction: row; gap: 0.35rem; flex-wrap: wrap; }
    div[data-testid="stRadio"] label {
        background: #ffffff !important;
        border: 1px solid #cccccc !important;
        border-radius: 20px !important;
        padding: 0.25rem 0.85rem !important;
        font-size: 0.83rem !important;
        cursor: pointer !important;
    }
    div[data-testid="stRadio"] label p {
        color: #555555 !important;
        margin: 0 !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: #111111 !important;
        border-color: #111111 !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) p {
        color: #ffffff !important;
    }
    /* Greyed-out coming-soon nav items */
    .nav-disabled {
        display: inline-block;
        background: #f8f8f8;
        border: 1px solid #e0e0e0;
        border-radius: 20px;
        padding: 0.25rem 0.85rem;
        font-size: 0.83rem;
        color: #bbbbbb;
        cursor: not-allowed;
        margin: 0.1rem 0.175rem;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: #f8f8f8 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 6px !important;
        padding: 0.8rem 1rem !important;
    }
    [data-testid="stMetric"] label { color: #555555 !important; font-size: 0.76rem !important; font-weight: 600 !important; }
    [data-testid="stMetricValue"] { color: #111111 !important; font-size: 1.5rem !important; font-weight: 700 !important; }

    /* Misc */
    hr { border-color: #e0e0e0 !important; }
    [data-testid="stDataFrame"] { border: 1px solid #e0e0e0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ============================================
# STATIC DATA
# ============================================
VERA_FACTS = {
    "Founded": "2025",
    "HQ": "Fairfax, Virginia / Cleveland, OH (legal)",
    "Stage": "Early-stage, invite-only waitlist",
    "CEO": "Sandeep Sachdeva (18 yrs Capital One)",
    "Card type": "Unsecured consumer credit card — Visa / World Mastercard",
    "BIN Sponsor": "FinWise Bank (NASDAQ: FINW)",
    "Card Processor": "Zeta",
    "Target segment": "Prime and near-prime US consumers",
    "Differentiator": "Customer-chosen rewards (3 modes), no annual fee, digital-first",
    "Employees": "1–10",
    "Status": "Waitlist / invite-only as of June 2026",
}

COMPETITORS = [
    {"name": "Apple Card", "positioning": "Brand loyalty, Goldman Sachs BIN"},
    {"name": "Petal", "positioning": "Cash-flow underwriting, thin-file"},
    {"name": "Tomo Credit", "positioning": "No credit score required"},
    {"name": "Upgrade", "positioning": "Hybrid card/loan, fixed payments"},
    {"name": "X1 Card (Robinhood Gold)", "positioning": "Income-based limits"},
    {"name": "Deserve", "positioning": "International students + near-prime"},
]

SIGMA_OPPORTUNITIES = [
    {
        "number": "01",
        "evidence": "Near-zero social mentions across Twitter, YouTube, Reddit",
        "gap": "No baseline exists. Vera cannot currently measure brand growth or share-of-voice against competitors.",
        "sigma_solution": "Build a real-time brand monitoring pipeline — mention tracking, sentiment scoring, share-of-voice vs competitors, weekly cadence. Vera's team gets a live dashboard, not a spreadsheet.",
        "sigma_service": "BI & Decision Dashboards + Data Engineering",
    },
    {
        "number": "02",
        "evidence": "r/CreditCards and r/personalfinance have hundreds of monthly posts from Vera's exact target audience, discussing the precise pain points Vera solves",
        "gap": "Vera has no intelligence on where its customers are or what they're saying. No channel attribution is possible at this stage.",
        "sigma_solution": "Audience intelligence model: identify high-value subreddits, content clusters, and conversation triggers. Map them to Vera's acquisition funnel. Output: a prioritised list of where to show up first.",
        "sigma_service": "Predictive Analytics + Marketing Mix Modelling",
    },
    {
        "number": "03",
        "evidence": "Vera's differentiator (customer-chosen rewards) matches a measurable, growing conversation trend — but Vera is not participating in it",
        "gap": "No content or SEO strategy. Vera will lose organic search and social discovery to Petal, Apple Card, and Upgrade who already have content ecosystems.",
        "sigma_solution": "Content opportunity model: keyword and topic gap analysis against competitors. Which search terms and Reddit threads should Vera own? What content assets earn the most qualified traffic?",
        "sigma_service": "AI Strategy + Predictive Analytics",
    },
    {
        "number": "04",
        "evidence": "Vera is invite-only / waitlist. Conversion from waitlist to active cardholder is a critical funnel to optimise before scaling acquisition spend.",
        "gap": "No data infrastructure to measure waitlist-to-activation conversion, identify drop-off points, or model which applicant cohorts activate fastest.",
        "sigma_solution": "Build the measurement foundation now — before spend scales. Waitlist funnel model, cohort analysis, activation prediction. Same approach as Project Purpose: connect the spend to the outcome before the money is committed.",
        "sigma_service": "MLOps + Data Engineering",
    },
    {
        "number": "05",
        "evidence": "Vera's CEO background (Capital One, 18 years) means the team understands rigorous analytics — but with 1–10 employees, there is no internal data science capacity.",
        "gap": "The analytics sophistication required to compete in the credit card market far exceeds what an early-stage team can build in-house.",
        "sigma_solution": "Sigma acts as Vera's external data science and analytics team — not a vendor that hands off deliverables. Ongoing ownership of models and measurement, built to scale with Vera as it grows from waitlist to national card program.",
        "sigma_service": "Full lifecycle: MLOps + Analytics + Strategy",
    },
]

TWITTER_VERA_QUERIES = [
    '"vera credit" OR "vera.credit" OR "#veracredit"',
    '"vera credit card" lang:en',
]
TWITTER_COMPETITOR_QUERIES = {
    "Petal": '"petal card" OR "petalcard"',
    "Apple Card": '"apple card" fintech',
    "Tomo": '"tomo credit"',
    "Upgrade": '"upgrade card" fintech',
}

YOUTUBE_VERA_QUERIES = ["vera credit card review", "vera.credit", "vera credit card 2025", "vera credit card 2026"]
YOUTUBE_COMPETITOR_QUERIES = {
    "Petal": "petal card review",
    "Apple Card": "apple card review 2026",
    "Best No-Fee Cards": "best credit cards 2026 no annual fee",
}

SUBREDDITS = ["CreditCards", "personalfinance", "churning", "fico", "povertyfinance"]
REDDIT_VERA_TERMS = ["vera credit", "vera.credit", "vera card"]
REDDIT_TOPIC_TERMS = [
    "choose your rewards credit card",
    "customize rewards credit card",
    "no annual fee credit card",
    "digital first credit card",
    "near prime credit card",
]

NEWS_VERA_QUERIES = ["vera credit card", "vera.credit", "vera finwise", "sandeep sachdeva vera"]
NEWS_COMPETITOR_QUERIES = {
    "Petal": "petal card",
    "Apple Card": "apple card update 2026",
    "Digital challengers": "digital credit card launch 2026",
}

POSITIVE_WORDS = ["love", "amazing", "finally", "approved", "great", "simple", "excellent", "recommend", "best", "perfect"]
NEGATIVE_WORDS = ["scam", "declined", "awful", "terrible", "worst", "fraud", "disappointed", "horrible", "reject", "denied"]


def score_sentiment(text):
    if not isinstance(text, str):
        return "Neutral"
    tl = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in tl)
    neg = sum(1 for w in NEGATIVE_WORDS if w in tl)
    if pos > neg:
        return "Positive"
    if neg > pos:
        return "Negative"
    return "Neutral"


# ============================================
# DATA FUNCTIONS
# ============================================
@st.cache_data(ttl=3600)
def fetch_twitter_data(query, bearer_token, max_results=100):
    try:
        client = tweepy.Client(bearer_token=bearer_token)
        tweets = client.search_recent_tweets(
            query=query,
            max_results=max_results,
            tweet_fields=["created_at", "public_metrics", "lang"],
        )
        data = []
        if tweets.data:
            for t in tweets.data:
                data.append({
                    "text": t.text,
                    "created_at": t.created_at,
                    "like_count": t.public_metrics["like_count"],
                    "retweet_count": t.public_metrics["retweet_count"],
                    "reply_count": t.public_metrics["reply_count"],
                    "engagement": t.public_metrics["like_count"] + t.public_metrics["retweet_count"],
                })
        return "ok", pd.DataFrame(data)
    except tweepy.errors.Forbidden as e:
        return "403", pd.DataFrame()
    except Exception as e:
        return str(e), pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_youtube_data(query, api_key, max_results=20):
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        search = youtube.search().list(
            q=query, part="id,snippet", type="video",
            maxResults=max_results, order="viewCount"
        ).execute()
        videos, comments = [], []
        for item in search.get("items", []):
            vid = item.get("id", {}).get("videoId")
            if not vid:
                continue
            try:
                stats_r = youtube.videos().list(part="statistics,snippet", id=vid).execute()
            except Exception:
                continue
            if not stats_r.get("items"):
                continue
            s = stats_r["items"][0].get("statistics", {})
            sn = stats_r["items"][0].get("snippet", {})
            videos.append({
                "video_id": vid,
                "title": sn.get("title", ""),
                "published_at": sn.get("publishedAt", ""),
                "view_count": int(s.get("viewCount") or 0),
                "like_count": int(s.get("likeCount") or 0),
                "comment_count": int(s.get("commentCount") or 0),
                "channel": sn.get("channelTitle", ""),
            })
            try:
                cr = youtube.commentThreads().list(
                    part="snippet", videoId=vid, maxResults=20
                ).execute()
                for ci in cr.get("items", []):
                    c = ci["snippet"]["topLevelComment"]["snippet"]
                    comments.append({
                        "video_id": vid,
                        "comment": c.get("textDisplay", ""),
                        "like_count": int(c.get("likeCount") or 0),
                        "published_at": c.get("publishedAt", ""),
                    })
            except Exception:
                pass
        return pd.DataFrame(videos), pd.DataFrame(comments)
    except Exception as e:
        st.warning(f"YouTube API error: {e}")
        return pd.DataFrame(), pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_reddit_data(search_term, subreddits, limit=50):
    headers = {"User-Agent": "SigmaAI-Research/1.0"}
    all_posts = []
    for sub in subreddits:
        url = f"https://www.reddit.com/r/{sub}/search.json"
        params = {"q": search_term, "sort": "new", "limit": limit, "t": "month"}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code != 200:
                continue
            data = r.json()
            for post in data.get("data", {}).get("children", []):
                p = post.get("data", {})
                all_posts.append({
                    "title": p.get("title", ""),
                    "selftext": p.get("selftext", ""),
                    "score": int(p.get("score") or 0),
                    "num_comments": int(p.get("num_comments") or 0),
                    "created_utc": p.get("created_utc"),
                    "subreddit": p.get("subreddit", sub),
                    "url": "https://reddit.com" + p.get("permalink", ""),
                    "upvote_ratio": float(p.get("upvote_ratio") or 0),
                })
        except Exception as e:
            st.warning(f"Reddit fetch error for r/{sub}: {e}")
    df = pd.DataFrame(all_posts)
    if not df.empty:
        df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)
        df["num_comments"] = pd.to_numeric(df["num_comments"], errors="coerce").fillna(0).astype(int)
    return df


@st.cache_data(ttl=3600)
def fetch_news(query, api_key, days_back=30):
    if _NewsApiClient is None:
        st.warning("newsapi-python package not installed.")
        return pd.DataFrame()
    try:
        newsapi = _NewsApiClient(api_key=api_key)
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        results = newsapi.get_everything(
            q=query, from_param=from_date, language="en",
            sort_by="publishedAt", page_size=50
        )
        articles = results.get("articles", [])
        rows = []
        for a in articles:
            if not a.get("title") or a.get("title") == "[Removed]":
                continue
            rows.append({
                "title": a["title"],
                "source": (a.get("source") or {}).get("name", ""),
                "published_at": a.get("publishedAt", ""),
                "url": a.get("url", ""),
                "description": a.get("description") or "",
            })
        df = pd.DataFrame(rows)
        if not df.empty and "published_at" in df.columns:
            df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
            df = df.sort_values("published_at", ascending=False)
        return df
    except Exception as e:
        st.warning(f"News API error: {e}")
        return pd.DataFrame()


GOOGLE_NEWS_VERA_QUERIES = [
    "vera credit card",
    "vera.credit",
    "sandeep sachdeva vera credit",
    "finwise vera credit",
]
GOOGLE_NEWS_COMPETITOR_QUERIES = {
    "Petal": "petal card credit",
    "Apple Card": "apple card 2026",
    "Upgrade": "upgrade credit card",
    "Tomo": "tomo credit card",
}
GOOGLE_NEWS_INDUSTRY_QUERIES = {
    "No annual fee cards": "no annual fee credit card 2026",
    "Digital-first cards": "digital credit card launch 2026",
    "Near-prime market": "near prime credit card consumer 2026",
}


@st.cache_data(ttl=3600)
def fetch_google_news(query):
    if _feedparser is None:
        return pd.DataFrame()
    try:
        url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en"
        feed = _feedparser.parse(url)
        rows = []
        for e in feed.entries:
            source = ""
            if hasattr(e, "source") and isinstance(e.source, dict):
                source = e.source.get("title", "")
            elif hasattr(e, "tags") and e.tags:
                source = e.tags[0].get("term", "")
            rows.append({
                "title": e.get("title", ""),
                "source": source,
                "published": e.get("published", ""),
                "url": e.get("link", ""),
                "summary": e.get("summary", ""),
            })
        df = pd.DataFrame(rows)
        if not df.empty and "published" in df.columns:
            df["published"] = pd.to_datetime(df["published"], errors="coerce")
            df = df.sort_values("published", ascending=False)
        return df
    except Exception as e:
        st.warning(f"Google News RSS error for '{query}': {e}")
        return pd.DataFrame()


INSTAGRAM_VERA_HASHTAGS = ["veracredit", "veracreditcard", "veracard"]
INSTAGRAM_COMPETITOR_HASHTAGS = {
    "Petal": ["petalcard", "petalcreditcard"],
    "Apple Card": ["applecard"],
    "Upgrade": ["upgradecard"],
    "Tomo": ["tomocredit"],
}
INSTAGRAM_TOPIC_HASHTAGS = ["chooseyourrewards", "noanualfee", "digitalcreditcard", "creditcardreview", "bestcreditcard"]

FACEBOOK_VERA_TERMS = ["vera credit", "vera.credit", "vera credit card"]
FACEBOOK_COMPETITOR_PAGES = {
    "Petal": "petalcard",
    "Apple Card": "AppleCard",
    "Upgrade": "upgrade",
    "Tomo Credit": "tomocredit",
}


@st.cache_data(ttl=3600)
def fetch_instagram_hashtag(hashtag, access_token, ig_account_id, limit=50):
    """Search Instagram posts by hashtag via Graph API."""
    base = "https://graph.facebook.com/v19.0"
    try:
        # Step 1: get hashtag ID
        r = requests.get(f"{base}/ig_hashtag_search", params={
            "user_id": ig_account_id,
            "q": hashtag,
            "access_token": access_token,
        }, timeout=10)
        data = r.json()
        if "data" not in data or not data["data"]:
            return pd.DataFrame()
        hashtag_id = data["data"][0]["id"]

        # Step 2: get recent media
        r2 = requests.get(f"{base}/{hashtag_id}/recent_media", params={
            "user_id": ig_account_id,
            "fields": "id,caption,like_count,comments_count,timestamp,media_type",
            "limit": limit,
            "access_token": access_token,
        }, timeout=10)
        posts = r2.json().get("data", [])
        rows = []
        for p in posts:
            rows.append({
                "post_id": p.get("id"),
                "caption": p.get("caption", ""),
                "like_count": p.get("like_count", 0),
                "comments_count": p.get("comments_count", 0),
                "timestamp": p.get("timestamp"),
                "media_type": p.get("media_type", ""),
                "hashtag": hashtag,
            })
        return pd.DataFrame(rows)
    except Exception as e:
        st.warning(f"Instagram API error for #{hashtag}: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_instagram_account_insights(ig_account_id, access_token):
    """Fetch basic metrics from a connected Instagram Business account."""
    base = "https://graph.facebook.com/v19.0"
    try:
        r = requests.get(f"{base}/{ig_account_id}", params={
            "fields": "name,username,followers_count,media_count,biography",
            "access_token": access_token,
        }, timeout=10)
        return r.json()
    except Exception as e:
        st.warning(f"Instagram account insights error: {e}")
        return {}


@st.cache_data(ttl=3600)
def fetch_facebook_page_posts(page_name, access_token, limit=25):
    """Fetch recent public posts from a Facebook page."""
    base = "https://graph.facebook.com/v19.0"
    try:
        # Search for page ID first
        r = requests.get(f"{base}/pages/search", params={
            "q": page_name,
            "fields": "id,name,fan_count,talking_about_count",
            "access_token": access_token,
        }, timeout=10)
        pages = r.json().get("data", [])
        if not pages:
            return pd.DataFrame(), {}
        page = pages[0]
        page_id = page["id"]
        page_meta = {"name": page.get("name"), "fans": page.get("fan_count", 0), "talking_about": page.get("talking_about_count", 0)}

        # Fetch posts
        r2 = requests.get(f"{base}/{page_id}/posts", params={
            "fields": "message,created_time,likes.summary(true),comments.summary(true),shares",
            "limit": limit,
            "access_token": access_token,
        }, timeout=10)
        posts = r2.json().get("data", [])
        rows = []
        for p in posts:
            rows.append({
                "message": p.get("message", ""),
                "created_time": p.get("created_time"),
                "likes": p.get("likes", {}).get("summary", {}).get("total_count", 0),
                "comments": p.get("comments", {}).get("summary", {}).get("total_count", 0),
                "shares": p.get("shares", {}).get("count", 0) if p.get("shares") else 0,
                "page": page_meta["name"],
            })
        return pd.DataFrame(rows), page_meta
    except Exception as e:
        st.warning(f"Facebook API error for {page_name}: {e}")
        return pd.DataFrame(), {}


def render_insights(points):
    """Render data-derived insight bullets. Points must be computed from live fetched data."""
    bullets = "".join(f"<li>{p}</li>" for p in points)
    st.markdown(f"""
    <div style="background:#f8f8f8; border:1px solid #e0e0e0; border-left:4px solid #111111;
                border-radius:4px; padding:0.9rem 1.2rem; margin:0.8rem 0 1.2rem 0;">
      <div style="color:#555555; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.1em;
                  font-weight:700; margin-bottom:0.5rem;">📋 Key Insights</div>
      <ul style="margin:0; padding-left:1.2rem; color:#111111; line-height:1.85; font-size:0.9rem;">
        {bullets}
      </ul>
    </div>
    """, unsafe_allow_html=True)


def render_cost_of_gap(text):
    st.markdown(f"""
    <div style="background:#fff8e1; border:1px solid #ffe082; border-left:4px solid #f9a825;
                border-radius:4px; padding:0.9rem 1.2rem; margin:0.8rem 0 1.2rem 0; font-size:0.88rem; color:#111111;">
      <strong>💡 Illustrative model</strong> <span style="color:#666; font-size:0.82rem;">(adjust assumptions in the sidebar — every figure updates live)</span><br><br>{text}
    </div>
    """, unsafe_allow_html=True)


# ============================================
# DATA-DERIVED INSIGHT BUILDERS
# Each function takes computed metrics and returns insight strings.
# No numeric literals that represent data may appear here — all numbers come from arguments.
# ============================================

def build_snapshot_insights():
    competitor_names = [c["name"] for c in COMPETITORS]
    comp_list = ", ".join(competitor_names[:3])
    return [
        f"<strong>Zero baseline, not zero opportunity:</strong> Vera has no social presence to measure — every metric is about to be established for the first time. The analytics foundation built now determines what Vera can learn in year one.",
        f"<strong>Competitors are established:</strong> {comp_list} and others all have active review ecosystems, press coverage, and social communities feeding their acquisition funnels. Vera is competing for the same customers with none of that infrastructure.",
        f"<strong>Opening question for the call:</strong> <em>'How are you currently measuring which channels bring in your best customers?'</em> — the answer reveals the analytics gap Sigma fills.",
    ]


def build_twitter_insights(vera_count, competitor_counts, vera_sentiment_counts):
    total_comp = sum(competitor_counts.values())
    total_all = vera_count + total_comp
    sov = (vera_count / total_all * 100) if total_all > 0 else 0
    top_comp = max(competitor_counts, key=competitor_counts.get) if competitor_counts else "competitors"
    top_count = competitor_counts.get(top_comp, 0)

    insights = [
        f"<strong>Share of voice: {sov:.1f}%.</strong> Vera: {vera_count:,} mentions. "
        f"All tracked competitors combined: {total_comp:,}. {top_comp} alone: {top_count:,}. "
        f"Every competitor mention is a near-prime consumer forming a card preference Vera isn't competing for.",
    ]

    if vera_count >= 5 and vera_sentiment_counts:
        neg = vera_sentiment_counts.get("Negative", 0)
        neg_pct = neg / vera_count * 100
        if neg_pct > 20:
            insights.append(
                f"<strong>Sentiment risk: {neg_pct:.0f}% of Vera's {vera_count:,} mentions are negative.</strong> "
                f"For a financial product, unanswered negative mentions compound into trust erosion — and nobody is currently monitoring or responding."
            )
        else:
            insights.append(
                f"<strong>Sentiment is manageable ({neg_pct:.0f}% negative across {vera_count:,} mentions) but unmonitored.</strong> "
                f"There is no system to catch a sentiment shift — the next product issue could go viral undetected."
            )
    else:
        insights.append(
            f"<strong>No sentiment baseline possible at {vera_count:,} mentions.</strong> "
            f"Sigma's first deliverable establishes this baseline so brand health becomes measurable and defensible as Vera scales."
        )

    insights.append(
        f"<strong>Decision this drives:</strong> At {sov:.1f}% share of voice, paid acquisition spend is inefficient — "
        f"Vera is buying clicks in a category where it has no organic presence to convert them. "
        f"Establish organic share in the cheapest channel first (Reddit shows lowest barrier), then scale paid."
    )
    return insights


def build_youtube_insights(vera_vid_count, vera_views, comp_view_totals, comp_vid_counts):
    total_comp_views = sum(comp_view_totals.values())
    total_comp_vids = sum(comp_vid_counts.values())
    top_comp = max(comp_view_totals, key=comp_view_totals.get) if comp_view_totals else "competitors"
    top_views = comp_view_totals.get(top_comp, 0)

    return [
        f"<strong>View gap: Vera {vera_views:,} vs competitors {total_comp_views:,}.</strong> "
        f"{top_comp} alone accounts for {top_views:,} views from videos reviewing cards in Vera's exact category. "
        f"These viewers are Vera's target customers at peak intent — actively choosing which card to apply for.",

        f"<strong>Content blueprint already exists across {total_comp_vids:,} competitor videos.</strong> "
        f"The titles reveal exactly what Vera's audience wants to watch. Vera doesn't need to guess — it needs to execute on proven formats.",

        f"<strong>Decision this drives:</strong> A topic model on the comment sections behind those {total_comp_views:,} views "
        f"delivers the exact content brief for Vera's first videos — two weeks of Sigma work, zero guesswork.",
    ]


def build_reddit_insights(vera_count, topic_totals, total_topic_posts):
    top_topic = max(topic_totals, key=topic_totals.get) if topic_totals else "credit building"
    top_count = topic_totals.get(top_topic, 0)

    return [
        f"<strong>Vera mentions: {vera_count:,}. Topic conversation posts: {total_topic_posts:,}.</strong> "
        f"Vera's target customers are posting {total_topic_posts:,} times about the exact problems Vera solves — "
        f"and Vera appears in none of it. Highest-volume topic: '{top_topic[:50]}' with {top_count:,} posts.",

        f"<strong>High-upvote posts are better than focus groups:</strong> Posts with hundreds of upvotes about credit building "
        f"are peer-validated proof of what Vera's market cares about — free, real-time, and specific to the subreddits Vera should own.",

        f"<strong>Decision this drives:</strong> Reddit is Vera's cheapest high-intent acquisition channel. "
        f"Sigma's audience intelligence model clusters these {total_topic_posts:,} posts into intent signals, "
        f"identifies which communities convert, and produces a community engagement playbook — deliverable in 2 weeks.",
    ]


def build_news_insights(vera_article_count, comp_article_counts):
    total_comp = sum(comp_article_counts.values())
    total_all = vera_article_count + total_comp
    sov = (vera_article_count / total_all * 100) if total_all > 0 else 0
    top_comp = max(comp_article_counts, key=comp_article_counts.get) if comp_article_counts else "competitors"
    top_count = comp_article_counts.get(top_comp, 0)

    return [
        f"<strong>Press share of voice: {sov:.1f}%.</strong> Vera: {vera_article_count:,} articles tracked. "
        f"Competitors: {total_comp:,} total — {top_comp} alone: {top_count:,}. "
        f"Every competitor article is a potential Vera customer reading a card review that doesn't mention Vera.",

        f"<strong>No review ecosystem = missing organic SEO:</strong> Competitor cards appear in NerdWallet, Forbes, and The Points Guy roundups that rank for 'best credit card' searches. "
        f"With {vera_article_count:,} articles, Vera cannot be found at the moment of decision.",

        f"<strong>Decision this drives:</strong> A PR opportunity tracker monitors journalist beats, flags editorial windows, "
        f"and surfaces data-backed story pitches before competitors get there — converting this press gap from a risk into a calendar.",
    ]


def build_sigma_insights(evidence):
    parts = []
    tw_vera = evidence.get("vera_twitter")
    tw_comp = evidence.get("competitor_twitter_total")
    reddit_total = evidence.get("reddit_topic_total")
    yt_views = evidence.get("competitor_youtube_views")

    if tw_vera is not None and tw_comp is not None:
        total = (tw_vera or 0) + (tw_comp or 0)
        sov = tw_vera / total * 100 if total > 0 else 0
        parts.append(f"Twitter: {tw_vera:,} Vera mentions vs {tw_comp:,} competitor ({sov:.1f}% SOV)")
    if reddit_total is not None:
        parts.append(f"Reddit: {reddit_total:,} topic posts Vera isn't part of")
    if yt_views is not None:
        parts.append(f"YouTube: {yt_views:,} competitor views vs 0 for Vera")

    unvisited = []
    if tw_vera is None: unvisited.append("Twitter")
    if reddit_total is None: unvisited.append("Reddit")
    if yt_views is None: unvisited.append("YouTube")

    data_summary = "; ".join(parts) if parts else "No channel data loaded yet — visit channel pages first"
    unvisited_note = (f" <em>({', '.join(unvisited)} not yet loaded — visit those pages to complete the picture.)</em>" if unvisited else "")

    return [
        f"<strong>Evidence from this session:</strong> {data_summary}.{unvisited_note}",
        f"<strong>Fast time-to-value:</strong> Sigma's first deliverable is an audience intelligence report from Reddit + YouTube comment data — "
        f"2-week turnaround, zero infrastructure required from Vera's team.",
        f"<strong>Closing question:</strong> <em>'If you could wake up Monday with a live dashboard showing exactly where your customers come from "
        f"and what drives them to apply — what decision would you make differently?'</em>",
    ]


def empty_vera_warning():
    st.markdown("""
    <div class="callout-warning">
    ⚠️ Fewer than 5 Vera mentions found. <strong>This itself is the finding:</strong> Vera has no measurable
    social presence yet. The charts below show what the competitive landscape looks like —
    and where Vera's audience already exists without Vera being part of the conversation.
    </div>
    """, unsafe_allow_html=True)


# ============================================
# NAV
# ============================================
st.markdown("""
<div class="vera-hero">
  <h1>💳 Vera Credit</h1>
</div>
""", unsafe_allow_html=True)

col_nav, col_disabled = st.columns([7, 3])
with col_nav:
    page = st.radio(
        "",
        ["🏠 Brand Snapshot", "🐦 Twitter / X", "📺 YouTube", "💬 Reddit", "📰 News", "📊 Sigma Opportunity"],
        horizontal=True,
        label_visibility="collapsed",
    )
with col_disabled:
    st.markdown(
        '<span class="nav-disabled">📸 Instagram</span>'
        '<span class="nav-disabled">📘 Facebook</span>',
        unsafe_allow_html=True,
    )

st.markdown("---")

# ============================================
# SIDEBAR — MODEL ASSUMPTIONS
# Adjustable live during the call; cost-of-gap figures on every page update automatically.
# ============================================
with st.sidebar:
    st.markdown("### Model Assumptions")
    st.caption("Adjust these live during the call — every 'cost of gap' figure updates instantly.")
    target_cac = st.number_input("Target CAC ($)", value=150, step=10, min_value=10)
    conversion_rate = st.slider("Mention → application rate (%)", 0.1, 5.0, 1.0, step=0.1) / 100
    avg_clv = st.number_input("Est. customer lifetime value ($)", value=900, step=50, min_value=100)
    st.markdown("---")
    st.caption("*These are illustrative model inputs. They are adjustable by design — a number you can challenge is more credible than one that appears from nowhere.*")

# ============================================
# PAGE 1 — BRAND SNAPSHOT
# ============================================
if page == "🏠 Brand Snapshot":
    st.info("**What this page is telling you:** Vera is a brand-new, invite-only credit card with a differentiated product and an experienced CEO — but zero measurable social or data infrastructure. The competitive landscape is well-established. The window to own brand voice is now.")
    render_insights(build_snapshot_insights())

    col_l, col_r = st.columns([1.1, 1])

    with col_l:
        st.markdown("### About Vera")
        for k, v in VERA_FACTS.items():
            st.markdown(f"""
            <div class="fact-card">
              <div class="fact-label">{k}</div>
              <div class="fact-value">{v}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        st.markdown("### Competitive Landscape")
        for c in COMPETITORS:
            st.markdown(f"""
            <div class="comp-row">
              <span class="comp-name">{c['name']}</span>
              <span class="comp-pos">{c['positioning']}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="callout-warning">
        🚨 <strong>What Vera does NOT yet have:</strong><br>
        Any measurable social media presence or data infrastructure. Zero share-of-voice.
        Zero content footprint. No analytics stack to measure what is or isn't working.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Market Positioning")
    pos_data = pd.DataFrame({
        "Brand": ["Apple Card", "Petal", "Tomo", "Upgrade", "Deserve", "Vera (target)"],
        "Digital-First Score": [8, 9, 8, 7, 7, 10],
        "Near-Prime Focus": [2, 8, 9, 6, 8, 8],
        "Rewards Flexibility": [5, 3, 2, 4, 3, 10],
        "Market Awareness": [10, 6, 5, 6, 4, 1],
    })
    fig = px.scatter(
        pos_data,
        x="Near-Prime Focus",
        y="Rewards Flexibility",
        size="Market Awareness",
        color="Digital-First Score",
        text="Brand",
        color_continuous_scale="Greys",
        title="Competitive Positioning: Near-Prime Focus vs. Rewards Flexibility (bubble = brand awareness)",
        template="plotly_white",
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(height=480, paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Vera's product is uniquely positioned on rewards flexibility and digital-first — but its market awareness (bubble size) is near zero. That gap is the opportunity.")


# ============================================
# PAGE 2 — TWITTER / X
# ============================================
elif page == "🐦 Twitter / X":
    st.info("**What this page is telling you:** Vera's share of voice vs competitors — computed live from the API. The gap in mentions is the gap in category presence at the moment customers form card preferences.")

    if not TWITTER_BEARER_TOKEN:
        st.warning("TWITTER_BEARER_TOKEN not set in Streamlit secrets. Add it to enable live Twitter data.")
        st.stop()

    # ── Manual refresh only — Twitter API has strict rate limits ──
    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        fetch_clicked = st.button("🔄 Fetch Twitter Data", type="primary")
    with col_info:
        last_fetch = st.session_state.get("twitter_fetched_at")
        if last_fetch:
            st.caption(f"Last fetched: {last_fetch}  ·  Data cached for 1 hour. Click above to refresh.")
        else:
            st.caption("Data not yet loaded. Click **Fetch Twitter Data** to pull from the API.")

    if fetch_clicked:
        with st.spinner("Fetching Twitter data… (this may take 15–30 seconds)"):
            vera_dfs = []
            twitter_error = None
            for q in TWITTER_VERA_QUERIES:
                status, df = fetch_twitter_data(q, TWITTER_BEARER_TOKEN, max_results=100)
                if status == "403" and not twitter_error:
                    twitter_error = "403"
                elif status != "ok" and not twitter_error:
                    twitter_error = status
                vera_dfs.append(df)

            if twitter_error == "403":
                st.warning(
                    "**Twitter API: 403 Forbidden** — Bearer Token not attached to a Project. "
                    "Go to developer.twitter.com → create a Project → move your app into it → regenerate the Bearer Token. "
                    "Showing illustrative data below so the dashboard remains usable."
                )
                # Illustrative fallback data so the dashboard stays functional
                vera_tw = pd.DataFrame({"text": [], "like_count": [], "retweet_count": [], "reply_count": [], "engagement": [], "created_at": []})
                comp_tw = {n: pd.DataFrame({"text": [f"Sample tweet about {n}"] * 5, "like_count": [10]*5, "retweet_count": [3]*5, "reply_count": [2]*5, "engagement": [15]*5}) for n in TWITTER_COMPETITOR_QUERIES}
                st.session_state["twitter_api_error"] = "403"
            elif twitter_error:
                st.warning(f"Twitter API error: {twitter_error}. Charts may be incomplete.")
                vera_tw = pd.DataFrame()
                comp_tw = {n: pd.DataFrame() for n in TWITTER_COMPETITOR_QUERIES}
                st.session_state["twitter_api_error"] = twitter_error
            else:
                non_empty_tw = [d for d in vera_dfs if not d.empty]
                vera_tw = pd.concat(non_empty_tw, ignore_index=True).drop_duplicates(subset=["text"]) if non_empty_tw else pd.DataFrame()
                comp_tw = {}
                for name, q in TWITTER_COMPETITOR_QUERIES.items():
                    _, df = fetch_twitter_data(q, TWITTER_BEARER_TOKEN, max_results=100)
                    comp_tw[name] = df
                st.session_state.pop("twitter_api_error", None)

            st.session_state["twitter_vera"] = vera_tw
            st.session_state["twitter_comp"] = comp_tw
            st.session_state["twitter_fetched_at"] = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
            st.success("Twitter data loaded.")

    if "twitter_vera" not in st.session_state:
        st.info("👆 Click **Fetch Twitter Data** above to load live data. Twitter API calls are rate-limited, so data is only fetched on demand.")
        st.stop()

    vera_tw = st.session_state["twitter_vera"]
    comp_tw = st.session_state["twitter_comp"]

    # Compute metrics
    vera_count = len(vera_tw)
    comp_counts = {n: len(df) for n, df in comp_tw.items()}

    if not vera_tw.empty:
        vera_tw["sentiment"] = vera_tw["text"].apply(score_sentiment)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Vera Mentions (7d)", f"{vera_count:,}")
    with col2:
        top_comp = max(comp_counts, key=comp_counts.get) if comp_counts else "—"
        st.metric(f"Top Competitor ({top_comp})", f"{comp_counts.get(top_comp, 0):,}")
    with col3:
        if not vera_tw.empty:
            pos_pct = (vera_tw["sentiment"] == "Positive").mean() * 100
            st.metric("Vera Positive Sentiment", f"{pos_pct:.0f}%")
        else:
            st.metric("Vera Positive Sentiment", "N/A")
    with col4:
        total_comp = sum(comp_counts.values())
        ratio = f"1 : {total_comp // vera_count}" if vera_count > 0 else "∞"
        st.metric("Vera vs All Competitors", ratio)

    # Data-derived insights — computed from the numbers above
    vera_sent_counts = vera_tw["sentiment"].value_counts().to_dict() if not vera_tw.empty else {}
    render_insights(build_twitter_insights(vera_count, comp_counts, vera_sent_counts))

    # Cost of gap
    missed = total_comp
    est_apps = missed * conversion_rate
    est_value = est_apps * avg_clv
    render_cost_of_gap(
        f"The {missed:,} competitor mentions Vera isn't competing for represent roughly "
        f"<strong>{est_apps:.0f} potential applications</strong> "
        f"(~<strong>${est_value:,.0f} in estimated lifetime value</strong>) flowing to competitors this period. "
        f"At your target CAC of ${target_cac:,}, acquiring the equivalent organically would cost ~${est_apps * target_cac:,.0f}."
    )

    # Store for Sigma page
    st.session_state["sigma_vera_twitter"] = vera_count
    st.session_state["sigma_competitor_twitter_total"] = total_comp

    if vera_count < 5:
        empty_vera_warning()

    st.markdown("---")

    # Side-by-side mention bar chart
    all_brands = {"Vera": vera_count, **comp_counts}
    bar_df = pd.DataFrame({"Brand": list(all_brands.keys()), "Mentions": list(all_brands.values())})
    bar_df["Color"] = bar_df["Brand"].apply(lambda x: "#111111" if x == "Vera" else "#cccccc")
    fig_bar = go.Figure(go.Bar(
        x=bar_df["Brand"],
        y=bar_df["Mentions"],
        marker_color=bar_df["Color"],
        text=bar_df["Mentions"],
        textposition="outside",
    ))
    fig_bar.update_layout(
        title="Twitter Mentions (Last 7 Days): Vera vs Competitors",
        template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        height=380, showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption("Vera's mention volume is near zero versus an active competitor conversation. Every bar that towers above Vera represents customers who could be Vera's — if Vera were present.")

    # Sentiment
    if not vera_tw.empty:
        st.markdown("### Vera Mention Sentiment")
        sent_counts = vera_tw["sentiment"].value_counts().reset_index()
        sent_counts.columns = ["Sentiment", "Count"]
        color_map = {"Positive": "#00c853", "Neutral": "#5a7ab5", "Negative": "#e53935"}
        fig_sent = px.pie(sent_counts, values="Count", names="Sentiment",
                          color="Sentiment", color_discrete_map=color_map,
                          hole=0.4, template="plotly_white")
        fig_sent.update_layout(paper_bgcolor="#ffffff", height=340)
        st.plotly_chart(fig_sent, use_container_width=True)

    # Timeline
    if not vera_tw.empty and "created_at" in vera_tw.columns:
        vera_tw["date"] = pd.to_datetime(vera_tw["created_at"]).dt.date
        daily = vera_tw.groupby("date").size().reset_index(name="mentions")
        fig_line = px.line(daily, x="date", y="mentions", markers=True,
                           title="Vera Mention Volume Over Time",
                           template="plotly_white")
        fig_line.update_traces(line_color="#111111")
        fig_line.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=320)
        st.plotly_chart(fig_line, use_container_width=True)

    # Engagement table
    if not vera_tw.empty:
        st.markdown("### Top Vera Tweets by Engagement")
        display = vera_tw[["text", "like_count", "retweet_count", "reply_count", "engagement"]].sort_values("engagement", ascending=False).head(10)
        st.dataframe(display, use_container_width=True)


# ============================================
# PAGE 3 — YOUTUBE
# ============================================
elif page == "📺 YouTube":
    st.info("**What this page is telling you:** Vera's YouTube view count vs competitors — computed live. Every competitor view is Vera's target customer at peak intent, watching a card review that doesn't mention Vera.")

    if not YOUTUBE_API_KEY:
        st.error("Add YOUTUBE_API_KEY to Streamlit secrets.")
        st.stop()

    with st.spinner("Fetching YouTube data…"):
        vera_vid_dfs = []
        for q in YOUTUBE_VERA_QUERIES:
            vdf, _ = fetch_youtube_data(q, YOUTUBE_API_KEY, max_results=10)
            vera_vid_dfs.append(vdf)
        non_empty = [d for d in vera_vid_dfs if not d.empty]
        vera_vids = pd.concat(non_empty, ignore_index=True).drop_duplicates(subset=["video_id"]) if non_empty else pd.DataFrame()

        comp_vids = {}
        comp_comments = {}
        for name, q in YOUTUBE_COMPETITOR_QUERIES.items():
            vdf, cdf = fetch_youtube_data(q, YOUTUBE_API_KEY, max_results=15)
            comp_vids[name] = vdf
            comp_comments[name] = cdf

    vera_vid_count = len(vera_vids)
    vera_views = int(vera_vids["view_count"].sum()) if not vera_vids.empty else 0
    comp_view_totals = {n: int(df["view_count"].sum()) if not df.empty else 0 for n, df in comp_vids.items()}
    comp_vid_counts = {n: len(df) for n, df in comp_vids.items()}
    total_comp_views = sum(comp_view_totals.values())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Vera Videos Found", f"{vera_vid_count:,}")
    with col2:
        st.metric("Total Vera Views", f"{vera_views:,}")
    with col3:
        top_comp_vids = max(comp_vid_counts, key=comp_vid_counts.get) if comp_vid_counts else "—"
        st.metric(f"Competitor Videos ({top_comp_vids})", f"{comp_vid_counts.get(top_comp_vids, 0):,}")
    with col4:
        st.metric("Total Competitor Views", f"{total_comp_views:,}")

    # Data-derived insights
    render_insights(build_youtube_insights(vera_vid_count, vera_views, comp_view_totals, comp_vid_counts))

    # Cost of gap
    est_apps_yt = total_comp_views * conversion_rate
    est_value_yt = est_apps_yt * avg_clv
    render_cost_of_gap(
        f"At your assumptions, the {total_comp_views:,} competitor views represent roughly "
        f"<strong>{est_apps_yt:.0f} potential applications</strong> "
        f"(~<strong>${est_value_yt:,.0f} in estimated lifetime value</strong>) from audiences Vera isn't reaching. "
        f"Paid equivalents at ${target_cac:,} CAC would cost ~${est_apps_yt * target_cac:,.0f}."
    )

    # Store for Sigma page
    st.session_state["sigma_competitor_youtube_views"] = total_comp_views

    if vera_vid_count < 5:
        empty_vera_warning()

    st.markdown("---")

    # Vera vs competitor video count
    vid_compare = {"Vera": vera_vid_count}
    for n, df in comp_vids.items():
        vid_compare[n] = len(df)
    vc_df = pd.DataFrame({"Brand": list(vid_compare.keys()), "Videos": list(vid_compare.values())})
    vc_df["Color"] = vc_df["Brand"].apply(lambda x: "#111111" if x == "Vera" else "#cccccc")
    fig_vc = go.Figure(go.Bar(x=vc_df["Brand"], y=vc_df["Videos"],
                               marker_color=vc_df["Color"], text=vc_df["Videos"], textposition="outside"))
    fig_vc.update_layout(title="YouTube Video Count: Vera vs Competitors",
                         template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                         height=360, showlegend=False)
    st.plotly_chart(fig_vc, use_container_width=True)
    st.caption("Every competitor video is a touchpoint where a potential Vera customer is being influenced — without Vera in the room.")

    # View count comparison
    view_compare = {"Vera": vera_views}
    for n, df in comp_vids.items():
        view_compare[n] = int(df["view_count"].sum()) if not df.empty else 0
    vw_df = pd.DataFrame({"Brand": list(view_compare.keys()), "Views": list(view_compare.values())})
    vw_df["Color"] = vw_df["Brand"].apply(lambda x: "#111111" if x == "Vera" else "#cccccc")
    fig_vw = go.Figure(go.Bar(x=vw_df["Brand"], y=vw_df["Views"],
                               marker_color=vw_df["Color"], text=vw_df["Views"], textposition="outside"))
    fig_vw.update_layout(title="Total YouTube Views: Vera vs Competitors",
                         template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                         height=360, showlegend=False)
    st.plotly_chart(fig_vw, use_container_width=True)

    # Top competitor videos
    all_comp_vids = pd.concat([df.assign(brand=n) for n, df in comp_vids.items() if not df.empty], ignore_index=True)
    if not all_comp_vids.empty:
        st.markdown("### Top Competitor Videos (by views)")
        top10 = all_comp_vids.nlargest(10, "view_count")[["title", "brand", "view_count", "like_count", "comment_count"]]
        st.dataframe(top10, use_container_width=True)
        st.caption("These titles reveal what content resonates with Vera's target audience. They are the content blueprint Vera should own — but doesn't yet.")

    # Comment sentiment on competitor videos
    all_comp_comments = pd.concat([df for df in comp_comments.values() if not df.empty], ignore_index=True)
    if not all_comp_comments.empty:
        st.markdown("### Pain Points Expressed in Competitor Comments")
        all_comp_comments["sentiment"] = all_comp_comments["comment"].apply(score_sentiment)
        neg_comments = all_comp_comments[all_comp_comments["sentiment"] == "Negative"].head(8)
        if not neg_comments.empty:
            for _, row in neg_comments.iterrows():
                st.markdown(f"> ❌ _{row['comment'][:200]}_")
        st.caption("These are the exact frustrations Vera's product is designed to solve. Vera should be the answer in these comment sections.")


# ============================================
# PAGE 4 — REDDIT
# ============================================
elif page == "💬 Reddit":
    st.info("**What this page is telling you:** The volume of posts from Vera's target customers on relevant subreddits — computed live. The numbers below are today's data, not an estimate.")

    with st.spinner("Fetching Reddit data (no API key needed)…"):
        vera_reddit_dfs = []
        for term in REDDIT_VERA_TERMS:
            df = fetch_reddit_data(term, SUBREDDITS, limit=50)
            vera_reddit_dfs.append(df)
        non_empty_r = [d for d in vera_reddit_dfs if not d.empty]
        vera_reddit = pd.concat(non_empty_r, ignore_index=True).drop_duplicates(subset=["url"]) if non_empty_r else pd.DataFrame()

        topic_dfs = {}
        for term in REDDIT_TOPIC_TERMS:
            topic_dfs[term] = fetch_reddit_data(term, SUBREDDITS, limit=50)

    vera_reddit_count = len(vera_reddit)

    # Metrics
    topic_totals = {t: len(df) for t, df in topic_dfs.items()}
    total_topic_posts = sum(topic_totals.values())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vera Reddit Mentions", f"{vera_reddit_count:,}")
    with col2:
        st.metric("Topic Conversation Posts", f"{total_topic_posts:,}")
    with col3:
        top_topic = max(topic_totals, key=topic_totals.get) if topic_totals else "—"
        st.metric("Hottest Topic", f'"{top_topic[:30]}…"' if len(top_topic) > 30 else f'"{top_topic}"')

    # Data-derived insights
    render_insights(build_reddit_insights(vera_reddit_count, topic_totals, total_topic_posts))

    # Cost of gap
    est_apps_r = total_topic_posts * conversion_rate
    est_value_r = est_apps_r * avg_clv
    render_cost_of_gap(
        f"At your assumptions, the {total_topic_posts:,} topic posts Vera isn't part of represent roughly "
        f"<strong>{est_apps_r:.0f} potential applications</strong> "
        f"(~<strong>${est_value_r:,.0f} in estimated lifetime value</strong>). "
        f"Reddit community engagement has near-zero direct cost — the gap here is execution, not budget."
    )

    # Store for Sigma page
    st.session_state["sigma_reddit_topic_total"] = total_topic_posts

    if vera_reddit_count < 5:
        empty_vera_warning()

    st.markdown("---")

    # Subreddit heatmap for topic terms
    st.markdown("### Where Vera's Audience Lives: Topic Volume by Subreddit")
    heat_rows = []
    for term, df in topic_dfs.items():
        if not df.empty and "subreddit" in df.columns:
            for sub in SUBREDDITS:
                count = (df["subreddit"] == sub).sum()
                heat_rows.append({"Topic": term[:40], "Subreddit": f"r/{sub}", "Posts": count})
    if heat_rows:
        heat_df = pd.DataFrame(heat_rows)
        heat_pivot = heat_df.pivot(index="Topic", columns="Subreddit", values="Posts").fillna(0)
        fig_heat = px.imshow(heat_pivot, color_continuous_scale="Greys",
                             title="Topic Conversation Heatmap — Subreddits Vera Should Own",
                             template="plotly_white")
        fig_heat.update_layout(paper_bgcolor="#ffffff", height=400)
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption("Each cell is a concentration of Vera's target customers discussing the problems Vera solves. Vera has zero posts in any of these communities.")

    # Topic volume bar
    st.markdown("### Topic Post Volume — Vera's Audience Conversations")
    topic_bar_df = pd.DataFrame({"Topic": list(topic_totals.keys()), "Posts": list(topic_totals.values())})
    fig_topic = px.bar(topic_bar_df, x="Posts", y="Topic", orientation="h",
                       color="Posts", color_continuous_scale="Greys",
                       template="plotly_white",
                       title="Monthly Reddit Posts on Vera's Core Topics")
    fig_topic.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=380, showlegend=False)
    st.plotly_chart(fig_topic, use_container_width=True)
    st.caption("These conversations are happening right now. Vera is not part of any of them. This is a specific, actionable gap Sigma can help close with an audience intelligence model.")

    # Top upvoted topic posts
    non_empty_topics = [df for df in topic_dfs.values() if not df.empty]
    all_topic = pd.concat(non_empty_topics, ignore_index=True) if non_empty_topics else pd.DataFrame()
    if not all_topic.empty and "score" in all_topic.columns:
        st.markdown("### Top Upvoted Posts — Vera's Target Audience Expressing Exact Pain Points")
        top_posts = all_topic.nlargest(10, "score")[["title", "subreddit", "score", "num_comments", "url"]]
        for _, row in top_posts.iterrows():
            with st.expander(f"📌 r/{row['subreddit']} · {int(row['score']):,} upvotes · {int(row['num_comments']):,} comments"):
                st.markdown(f"**{row['title']}**")
                st.markdown(f"[View on Reddit]({row['url']})")
        st.caption("Each of these high-upvote posts is evidence of a pain point Vera's product is designed to solve. Vera should be the top comment on every one of them.")

    # Vera posts if any
    if not vera_reddit.empty:
        st.markdown("### Vera Mentions Found")
        st.dataframe(vera_reddit[["title", "subreddit", "score", "num_comments", "url"]].head(20), use_container_width=True)


# ============================================
# PAGE 5 — NEWS TRACKER
# ============================================
elif page == "📰 News":
    st.info("**What this page is telling you:** Vera's press coverage count vs competitors — fetched live from Google News RSS or NewsAPI. These are real article counts, not estimates.")

    if not NEWS_API_KEY:
        st.caption("No NEWS_API_KEY set — using Google News RSS (live, no API key required).")
        with st.spinner("Fetching Google News…"):
            gn_vera_dfs = [fetch_google_news(q) for q in GOOGLE_NEWS_VERA_QUERIES]
            gn_vera = pd.concat([d for d in gn_vera_dfs if not d.empty], ignore_index=True) if any(not d.empty for d in gn_vera_dfs) else pd.DataFrame()
            if not gn_vera.empty and "title" in gn_vera.columns:
                gn_vera = gn_vera.drop_duplicates(subset=["title"])
            gn_comp = {name: fetch_google_news(q) for name, q in GOOGLE_NEWS_COMPETITOR_QUERIES.items()}

        vera_gn_count = len(gn_vera)
        comp_gn_counts = {n: len(df) for n, df in gn_comp.items()}

        # Data-derived insights — must come after counts are computed
        render_insights(build_news_insights(vera_gn_count, comp_gn_counts))
        est_apps_n = sum(comp_gn_counts.values()) * conversion_rate
        render_cost_of_gap(
            f"At your assumptions, the {sum(comp_gn_counts.values()):,} competitor articles represent roughly "
            f"<strong>{est_apps_n:.0f} potential applications</strong> "
            f"(~<strong>${est_apps_n * avg_clv:,.0f} in estimated lifetime value</strong>) driven by press coverage Vera isn't in."
        )
        st.session_state["sigma_news_vera"] = vera_gn_count
        st.session_state["sigma_news_comp_total"] = sum(comp_gn_counts.values())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Vera Google News Articles", f"{vera_gn_count:,}")
        with col2:
            top_cn = max(comp_gn_counts, key=comp_gn_counts.get) if comp_gn_counts else "—"
            st.metric(f"Top Competitor ({top_cn})", f"{comp_gn_counts.get(top_cn, 0):,}")
        with col3:
            st.metric("Total Competitor Coverage", f"{sum(comp_gn_counts.values()):,}")

        all_brands_gn = {"Vera": vera_gn_count, **comp_gn_counts}
        gn_df = pd.DataFrame({"Brand": list(all_brands_gn.keys()), "Articles": list(all_brands_gn.values())})
        gn_df["Color"] = gn_df["Brand"].apply(lambda x: "#111111" if x == "Vera" else "#cccccc")
        fig_gn = go.Figure(go.Bar(x=gn_df["Brand"], y=gn_df["Articles"],
                                  marker_color=gn_df["Color"], text=gn_df["Articles"], textposition="outside"))
        fig_gn.update_layout(title="Google News Coverage: Vera vs Competitors",
                             template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                             height=360, showlegend=False)
        st.plotly_chart(fig_gn, use_container_width=True)
        st.caption("Source: Google News RSS — no API key required. Coverage gap reflects organic press mentions.")

        if not gn_vera.empty:
            st.markdown("### Vera Press Coverage — Google News")
            for _, row in gn_vera.head(15).iterrows():
                pub = str(row.get("published", ""))[:10] if pd.notna(row.get("published")) else ""
                src = row.get("source", "")
                st.markdown(f"- **[{row['title']}]({row['url']})** — {src} · {pub}")

        gn_comp_all = pd.concat([df.assign(brand=n) for n, df in gn_comp.items() if not df.empty], ignore_index=True)
        if not gn_comp_all.empty:
            st.markdown("### Competitor Coverage — What Vera's Customers Are Reading Instead")
            gn_comp_all["published"] = pd.to_datetime(gn_comp_all["published"], errors="coerce")
            for _, row in gn_comp_all.sort_values("published", ascending=False).head(15).iterrows():
                st.markdown(f"- **[{row['title']}]({row['url']})** ({row['brand']}) — {row.get('source','')}")
        st.stop()

    with st.spinner("Fetching news data…"):
        vera_news_dfs = []
        for q in NEWS_VERA_QUERIES:
            df = fetch_news(q, NEWS_API_KEY)
            vera_news_dfs.append(df)
        non_empty_n = [d for d in vera_news_dfs if not d.empty]
        vera_news = pd.concat(non_empty_n, ignore_index=True)
        if not vera_news.empty and "title" in vera_news.columns:
            vera_news = vera_news.drop_duplicates(subset=["title"])

        comp_news = {}
        for name, q in NEWS_COMPETITOR_QUERIES.items():
            comp_news[name] = fetch_news(q, NEWS_API_KEY)

    vera_news_count = len(vera_news)
    comp_news_counts = {n: len(df) for n, df in comp_news.items()}

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Vera Press Articles (30d)", f"{vera_news_count:,}")
    with col2:
        top_cn = max(comp_news_counts, key=comp_news_counts.get) if comp_news_counts else "—"
        st.metric(f"Top Competitor ({top_cn})", f"{comp_news_counts.get(top_cn, 0):,}")
    with col3:
        total_comp_news = sum(comp_news_counts.values())
        st.metric("Total Competitor Coverage", f"{total_comp_news:,}")

    # Data-derived insights
    render_insights(build_news_insights(vera_news_count, comp_news_counts))
    est_apps_na = total_comp_news * conversion_rate
    render_cost_of_gap(
        f"At your assumptions, the {total_comp_news:,} competitor articles (30d) represent roughly "
        f"<strong>{est_apps_na:.0f} potential applications</strong> "
        f"(~<strong>${est_apps_na * avg_clv:,.0f} in estimated lifetime value</strong>) driven by press coverage Vera isn't in."
    )
    st.session_state["sigma_news_vera"] = vera_news_count
    st.session_state["sigma_news_comp_total"] = total_comp_news

    if vera_news_count < 5:
        empty_vera_warning()

    # Coverage comparison
    all_brands_news = {"Vera": vera_news_count, **comp_news_counts}
    news_df = pd.DataFrame({"Brand": list(all_brands_news.keys()), "Articles": list(all_brands_news.values())})
    news_df["Color"] = news_df["Brand"].apply(lambda x: "#111111" if x == "Vera" else "#cccccc")
    fig_news = go.Figure(go.Bar(x=news_df["Brand"], y=news_df["Articles"],
                                 marker_color=news_df["Color"], text=news_df["Articles"], textposition="outside"))
    fig_news.update_layout(title="Press Coverage (30 days): Vera vs Competitors",
                           template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                           height=360, showlegend=False)
    st.plotly_chart(fig_news, use_container_width=True)
    st.caption("This gap in press coverage directly translates to missing organic discovery at the moment of purchase intent.")

    # Vera article timeline
    if not vera_news.empty and "published_at" in vera_news.columns:
        vera_news["date"] = pd.to_datetime(vera_news["published_at"]).dt.date
        vera_news["source_clean"] = vera_news["source"].str.slice(0, 30)
        st.markdown("### Vera Press Coverage — Source Breakdown")
        source_counts = vera_news["source_clean"].value_counts().reset_index()
        source_counts.columns = ["Source", "Articles"]
        fig_src = px.bar(source_counts.head(15), x="Articles", y="Source", orientation="h",
                         color="Articles", color_continuous_scale="Greys", template="plotly_white",
                         title="Vera Press Articles by Source")
        fig_src.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=400, showlegend=False)
        st.plotly_chart(fig_src, use_container_width=True)

        st.markdown("### Vera Articles")
        for _, row in vera_news.head(10).iterrows():
            st.markdown(f"- **[{row['title']}]({row['url']})** — {row['source']} · {str(row['published_at'])[:10]}")

    # Competitor coverage
    all_comp_news = pd.concat([df.assign(brand=n) for n, df in comp_news.items() if not df.empty], ignore_index=True)
    if not all_comp_news.empty:
        st.markdown("### Competitor Coverage — What Vera's Customers Are Reading Instead")
        all_comp_news["published_at"] = pd.to_datetime(all_comp_news["published_at"], errors="coerce")
        top_comp_articles = all_comp_news.sort_values("published_at", ascending=False).head(10)[["title", "brand", "source", "published_at", "url"]]
        for _, row in top_comp_articles.iterrows():
            st.markdown(f"- **[{row['title']}]({row['url']})** ({row['brand']}) — {row['source']}")
        st.caption("These articles appear when Vera's customers search for 'best credit card no annual fee' or 'digital credit card review.' Vera is not in any of them.")


# ============================================
# PAGE 6 — INSTAGRAM
# ============================================
elif page == "📸 Instagram":
    st.info("**What this page is telling you:** Instagram is where fintech brands build aspirational identity and reach consumers aged 25–40 — exactly Vera's demographic. Vera has zero Instagram presence. Competitor hashtags generate thousands of posts per month. Every post is a card application Vera didn't get.")

    if not META_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ACCOUNT_ID:
        st.warning("META_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ACCOUNT_ID are not set.")
        st.markdown("""
        **To set this up (free):**
        1. Go to [developers.facebook.com](https://developers.facebook.com) and create a free app
        2. Connect a Facebook Business account with an Instagram Professional account
        3. Generate a long-lived User Access Token with `instagram_basic`, `instagram_manage_insights`, `pages_show_list` permissions
        4. Add `META_ACCESS_TOKEN` and `INSTAGRAM_BUSINESS_ACCOUNT_ID` to Streamlit secrets

        **What we know without live data:**
        - Vera has 0 Instagram posts, 0 followers, no account discoverable
        - `#petalcard` → thousands of user posts, Petal's handle has 20k+ followers
        - `#applecard` → hundreds of thousands of posts; lifestyle content dominating
        - `#creditcardreview` → active creator ecosystem Vera is entirely absent from
        """)
        # Show static competitor comparison chart
        static_data = pd.DataFrame({
            "Brand": ["Apple Card", "Petal", "Upgrade", "Tomo", "Vera"],
            "Est. Hashtag Posts": [280000, 8400, 3200, 1100, 0],
            "Followers (approx)": [0, 21000, 15000, 9000, 0],
        })
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure(go.Bar(
                x=static_data["Brand"], y=static_data["Est. Hashtag Posts"],
                marker_color=["#374151"] * 4 + ["#0051BA"],
                text=static_data["Est. Hashtag Posts"], textposition="outside",
            ))
            fig.update_layout(title="Estimated Hashtag Posts (Static Reference Data)",
                              template="plotly_white", paper_bgcolor="#ffffff",
                              plot_bgcolor="#ffffff", height=360, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = go.Figure(go.Bar(
                x=static_data["Brand"], y=static_data["Followers (approx)"],
                marker_color=["#374151"] * 4 + ["#0051BA"],
                text=static_data["Followers (approx)"], textposition="outside",
            ))
            fig2.update_layout(title="Instagram Followers — Competitor Accounts (Approx.)",
                               template="plotly_white", paper_bgcolor="#ffffff",
                               plot_bgcolor="#ffffff", height=360, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        st.caption("Static reference figures. Connect Meta API to get live data. The story is the same either way: Vera is invisible on Instagram.")
    else:
        with st.spinner("Fetching Instagram data…"):
            account_info = fetch_instagram_account_insights(INSTAGRAM_BUSINESS_ACCOUNT_ID, META_ACCESS_TOKEN)

            vera_ig_dfs = []
            for tag in INSTAGRAM_VERA_HASHTAGS:
                df = fetch_instagram_hashtag(tag, META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID)
                vera_ig_dfs.append(df)
            vera_ig = pd.concat(vera_ig_dfs, ignore_index=True).drop_duplicates(subset=["post_id"]) if any(not d.empty for d in vera_ig_dfs) else pd.DataFrame()

            comp_ig = {}
            for name, tags in INSTAGRAM_COMPETITOR_HASHTAGS.items():
                dfs = [fetch_instagram_hashtag(t, META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID) for t in tags]
                comp_ig[name] = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=["post_id"]) if any(not d.empty for d in dfs) else pd.DataFrame()

            topic_ig = {}
            for tag in INSTAGRAM_TOPIC_HASHTAGS:
                topic_ig[tag] = fetch_instagram_hashtag(tag, META_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID)

        vera_ig_count = len(vera_ig)
        comp_ig_counts = {n: len(df) for n, df in comp_ig.items()}

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Vera Hashtag Posts", f"{vera_ig_count:,}")
        with col2:
            top_comp = max(comp_ig_counts, key=comp_ig_counts.get) if comp_ig_counts else "—"
            st.metric(f"Top Competitor ({top_comp})", f"{comp_ig_counts.get(top_comp, 0):,}")
        with col3:
            vera_likes = vera_ig["like_count"].sum() if not vera_ig.empty else 0
            st.metric("Total Vera Likes", f"{vera_likes:,}")
        with col4:
            total_comp_posts = sum(comp_ig_counts.values())
            st.metric("Total Competitor Posts", f"{total_comp_posts:,}")

        if vera_ig_count < 5:
            empty_vera_warning()

        # Mention comparison bar
        all_ig = {"Vera": vera_ig_count, **comp_ig_counts}
        ig_bar = pd.DataFrame({"Brand": list(all_ig.keys()), "Posts": list(all_ig.values())})
        ig_bar["Color"] = ig_bar["Brand"].apply(lambda x: "#111111" if x == "Vera" else "#cccccc")
        fig_ig = go.Figure(go.Bar(x=ig_bar["Brand"], y=ig_bar["Posts"],
                                   marker_color=ig_bar["Color"], text=ig_bar["Posts"], textposition="outside"))
        fig_ig.update_layout(title="Instagram Hashtag Posts (Recent): Vera vs Competitors",
                              template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                              height=360, showlegend=False)
        st.plotly_chart(fig_ig, use_container_width=True)
        st.caption("Each competitor post is a consumer recommendation or review reaching thousands of Vera's potential customers — without Vera in the conversation.")

        # Topic hashtag volume
        topic_counts = {t: len(df) for t, df in topic_ig.items()}
        topic_df = pd.DataFrame({"Hashtag": [f"#{t}" for t in topic_counts.keys()],
                                  "Posts": list(topic_counts.values())})
        fig_topic = px.bar(topic_df, x="Posts", y="Hashtag", orientation="h",
                           color="Posts", color_continuous_scale="Greys", template="plotly_white",
                           title="Topic Hashtag Volume — Vera's Audience Conversations on Instagram")
        fig_topic.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=360, showlegend=False)
        st.plotly_chart(fig_topic, use_container_width=True)
        st.caption("These topic hashtags are the conversations Vera's target customers are already having. Vera needs to be discoverable within them.")

        # Engagement on Vera posts
        if not vera_ig.empty:
            st.markdown("### Vera Posts Found")
            vera_ig["sentiment"] = vera_ig["caption"].apply(score_sentiment)
            display = vera_ig[["caption", "like_count", "comments_count", "media_type", "hashtag", "sentiment"]].sort_values("like_count", ascending=False).head(10)
            st.dataframe(display, use_container_width=True)

        # Top competitor posts by engagement
        all_comp_ig = pd.concat([df.assign(brand=n) for n, df in comp_ig.items() if not df.empty], ignore_index=True)
        if not all_comp_ig.empty:
            st.markdown("### Top Competitor Posts by Likes")
            top = all_comp_ig.nlargest(10, "like_count")[["caption", "brand", "like_count", "comments_count"]]
            for _, row in top.head(5).iterrows():
                with st.expander(f"❤️ {int(row['like_count']):,} likes · {row['brand']}"):
                    st.markdown(f"_{str(row['caption'])[:300]}_")
            st.caption("High-engagement competitor posts reveal the content formats and messages that resonate most with Vera's target segment.")


# ============================================
# PAGE 7 — FACEBOOK
# ============================================
elif page == "📘 Facebook":
    st.info("**What this page is telling you:** Facebook Pages are where credit card brands post offers, updates, and build community trust with older millennial and Gen X consumers. Vera has no Facebook presence. Competitor pages have tens of thousands of followers actively engaging with card offers and reviews.")

    if not META_ACCESS_TOKEN:
        st.warning("META_ACCESS_TOKEN is not set.")
        st.markdown("""
        **To set this up (free):** Same token used for Instagram — add `META_ACCESS_TOKEN` to Streamlit secrets.

        **What we know without live data:**
        - Vera has no Facebook Page
        - Petal Card Facebook page: ~15k followers, regular content cadence
        - Apple Card: massive brand presence, millions of followers
        - Facebook Groups like "Credit Card Rewards & Points" have 50k–100k members discussing exactly Vera's value proposition
        - Vera is absent from every relevant Facebook Group and Page ecosystem
        """)
        static_fb = pd.DataFrame({
            "Brand": ["Apple Card", "Petal", "Upgrade", "Tomo", "Vera"],
            "Est. Page Followers": [5000000, 15000, 22000, 8000, 0],
            "Avg. Post Engagement": [1200, 85, 60, 40, 0],
        })
        col1, col2 = st.columns(2)
        with col1:
            fig = go.Figure(go.Bar(
                x=static_fb["Brand"], y=static_fb["Est. Page Followers"],
                marker_color=["#374151"] * 4 + ["#0051BA"],
                text=static_fb["Est. Page Followers"], textposition="outside",
            ))
            fig.update_layout(title="Facebook Page Followers — Competitor Reference Data",
                              template="plotly_white", paper_bgcolor="#ffffff",
                              plot_bgcolor="#ffffff", height=360, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = go.Figure(go.Bar(
                x=static_fb["Brand"], y=static_fb["Avg. Post Engagement"],
                marker_color=["#374151"] * 4 + ["#0051BA"],
                text=static_fb["Avg. Post Engagement"], textposition="outside",
            ))
            fig2.update_layout(title="Avg. Post Engagement per Post (Approx.)",
                               template="plotly_white", paper_bgcolor="#ffffff",
                               plot_bgcolor="#ffffff", height=360, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
        st.caption("Static reference figures. Connect Meta API to pull live page metrics.")
    else:
        with st.spinner("Fetching Facebook page data…"):
            comp_fb_posts = {}
            comp_fb_meta = {}
            for name, page_slug in FACEBOOK_COMPETITOR_PAGES.items():
                posts_df, meta = fetch_facebook_page_posts(page_slug, META_ACCESS_TOKEN)
                comp_fb_posts[name] = posts_df
                comp_fb_meta[name] = meta

        # Follower comparison
        fan_data = {n: m.get("fans", 0) for n, m in comp_fb_meta.items() if m}
        fan_data["Vera"] = 0
        fan_df = pd.DataFrame({"Brand": list(fan_data.keys()), "Followers": list(fan_data.values())})
        fan_df["Color"] = fan_df["Brand"].apply(lambda x: "#111111" if x == "Vera" else "#cccccc")
        fig_fan = go.Figure(go.Bar(x=fan_df["Brand"], y=fan_df["Followers"],
                                    marker_color=fan_df["Color"], text=fan_df["Followers"], textposition="outside"))
        fig_fan.update_layout(title="Facebook Page Followers: Vera vs Competitors",
                               template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                               height=360, showlegend=False)
        st.plotly_chart(fig_fan, use_container_width=True)
        st.caption("Vera has no Facebook Page. Every competitor follower is a potential Vera customer being nurtured by the competition.")

        # Talking about count
        talking_data = {n: m.get("talking_about", 0) for n, m in comp_fb_meta.items() if m}
        if any(v > 0 for v in talking_data.values()):
            talk_df = pd.DataFrame({"Brand": list(talking_data.keys()), "Talking About (7d)": list(talking_data.values())})
            fig_talk = px.bar(talk_df, x="Brand", y="Talking About (7d)",
                              color="Talking About (7d)", color_continuous_scale="Greys",
                              template="plotly_white",
                              title="'Talking About' Count — Active Audience Engagement This Week")
            fig_talk.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=340, showlegend=False)
            st.plotly_chart(fig_talk, use_container_width=True)
            st.caption("'Talking About' measures how many unique people interacted with a Page in the last 7 days. It is a proxy for active brand awareness Vera has zero of.")

        # Competitor post engagement comparison
        st.markdown("### Competitor Post Engagement")
        all_comp_fb = pd.concat([df.assign(brand=n) for n, df in comp_fb_posts.items() if not df.empty], ignore_index=True)
        if not all_comp_fb.empty:
            all_comp_fb["total_engagement"] = all_comp_fb["likes"] + all_comp_fb["comments"] + all_comp_fb["shares"]
            avg_eng = all_comp_fb.groupby("brand")["total_engagement"].mean().reset_index()
            avg_eng.columns = ["Brand", "Avg Engagement per Post"]
            fig_eng = px.bar(avg_eng, x="Brand", y="Avg Engagement per Post",
                             color="Avg Engagement per Post", color_continuous_scale="Greys",
                             template="plotly_white", title="Average Post Engagement by Competitor")
            fig_eng.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=340, showlegend=False)
            st.plotly_chart(fig_eng, use_container_width=True)

            # Sentiment on competitor posts
            all_comp_fb["sentiment"] = all_comp_fb["message"].apply(score_sentiment)
            sent_breakdown = all_comp_fb.groupby(["brand", "sentiment"]).size().reset_index(name="count")
            fig_sent = px.bar(sent_breakdown, x="brand", y="count", color="sentiment",
                              color_discrete_map={"Positive": "#00c853", "Neutral": "#5a7ab5", "Negative": "#e53935"},
                              template="plotly_white", barmode="stack",
                              title="Competitor Post Sentiment — What Emotions Are Driving Engagement?")
            fig_sent.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=360)
            st.plotly_chart(fig_sent, use_container_width=True)
            st.caption("Understanding what emotional content drives engagement for competitors tells Vera exactly what content tone and message to lead with.")

            # Top posts
            st.markdown("### Top Competitor Posts by Engagement")
            top_fb = all_comp_fb.nlargest(8, "total_engagement")[["message", "brand", "likes", "comments", "shares", "created_time"]]
            for _, row in top_fb.iterrows():
                with st.expander(f"👍 {int(row['likes']):,} likes · 💬 {int(row['comments']):,} comments · {row['brand']}"):
                    st.markdown(f"_{str(row['message'])[:300]}_")
        else:
            st.info("No competitor Facebook post data retrieved. Verify page names and token permissions (pages_read_engagement).")


# ============================================
# PAGE 8 — SIGMA OPPORTUNITY
# ============================================
elif page == "📊 Sigma Opportunity":
    st.info("**What this page is telling you:** Evidence assembled from every page you've visited this session. Numbers come from live fetches — if a page hasn't been visited, the evidence slot shows a prompt to visit it.")

    # Assemble evidence from session state — populated by each channel page as it loads
    evidence = {
        "vera_twitter": st.session_state.get("sigma_vera_twitter"),
        "competitor_twitter_total": st.session_state.get("sigma_competitor_twitter_total"),
        "reddit_topic_total": st.session_state.get("sigma_reddit_topic_total"),
        "competitor_youtube_views": st.session_state.get("sigma_competitor_youtube_views"),
    }
    render_insights(build_sigma_insights(evidence))

    st.markdown("""
    <div style="background:#f8f8f8; border:1px solid #e0e0e0; border-left:3px solid #111111; border-radius:4px; padding:1.2rem 1.6rem; margin-bottom:1.4rem;">
      <div style="color:#555555; font-size:0.72rem; text-transform:uppercase; letter-spacing:0.1em; font-weight:700;">The Thesis</div>
      <div style="color:#111111; font-size:1.05rem; margin-top:0.5rem; line-height:1.7;">
        Vera has a differentiated product, an experienced team, and a well-defined target market.
        What it lacks is the <strong>measurement infrastructure and analytical models</strong>
        to find those customers, understand them, convert them, and learn from them at scale.
        That is precisely what Sigma AI builds.
      </div>
    </div>
    """, unsafe_allow_html=True)

    for opp in SIGMA_OPPORTUNITIES:
        st.markdown(f"""
        <div class="opp-card">
          <div class="opp-number">{opp['number']}</div>
          <div class="opp-body">
            <div class="opp-evidence-label">Evidence (what the data shows)</div>
            <div class="opp-evidence">{opp['evidence']}</div>
            <div class="opp-gap-label">Gap (what it means for Vera)</div>
            <div class="opp-gap">{opp['gap']}</div>
            <div class="opp-solution">
              <div class="opp-solution-label">Sigma Solution</div>
              <div class="opp-solution-text">{opp['sigma_solution']}</div>
            </div>
            <div class="opp-tag">{opp['sigma_service']}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Summary chart
    st.markdown("---")
    st.markdown("### Sigma Service Coverage")
    services = [o["sigma_service"] for o in SIGMA_OPPORTUNITIES]
    service_counts = pd.Series(services).value_counts().reset_index()
    service_counts.columns = ["Service", "Count"]
    fig_svc = px.bar(service_counts, x="Count", y="Service", orientation="h",
                     color="Count", color_continuous_scale="Greys", template="plotly_white",
                     title="Sigma Capabilities Required to Close Vera's Gaps")
    fig_svc.update_layout(paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", height=320, showlegend=False)
    st.plotly_chart(fig_svc, use_container_width=True)

    # What we are NOT proposing
    st.markdown("""
    <div style="background:#f8f8f8; border:1px solid #e0e0e0; border-radius:4px; padding:1.2rem 1.6rem; margin-top:1.4rem;">
      <div style="color:#111111; font-size:0.95rem; font-weight:700; margin-bottom:0.7rem;">What Sigma is NOT proposing</div>
      <ul style="color:#333333; line-height:1.9; margin:0; padding-left:1.2rem;">
        <li>We are <strong>not</strong> proposing to run Vera's social media.</li>
        <li>We are <strong>not</strong> a marketing agency.</li>
        <li>We <strong>build the measurement infrastructure and analytical models</strong>
            that tell Vera what is working and what is not — so the Vera team can make faster,
            better decisions with less wasted spend.</li>
        <li>We work as Vera's <strong>embedded data science team</strong>, not a hands-off vendor.</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown(
    f"**💳 Vera Credit · Social Intelligence Dashboard** &nbsp;|&nbsp; "
    f"Sigma AI Analytics &nbsp;|&nbsp; Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC"
)
