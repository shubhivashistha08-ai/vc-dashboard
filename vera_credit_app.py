import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tweepy
from googleapiclient.discovery import build
import requests

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
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,400;0,700;1,400&family=Inter:wght@300;400;500;600&display=swap');

    /* Global */
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

    /* Hero header */
    .vera-hero {
        background: linear-gradient(135deg, #0a0f1e 0%, #0d1b3e 60%, #0a1628 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem 2rem 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid #1a2a4a;
    }
    .vera-hero h1 {
        font-family: 'Fraunces', Georgia, serif;
        font-size: 2.4rem;
        color: #e8f0ff;
        margin: 0 0 0.3rem 0;
    }
    .vera-hero p { color: #8aa0c8; font-size: 1rem; margin: 0; }

    /* Fact card */
    .fact-card {
        background: #0d1b3e;
        border: 1px solid #1a2a4a;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
    }
    .fact-label { color: #5a7ab5; font-size: 0.78rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .fact-value { color: #e0eaff; font-size: 1rem; font-weight: 500; margin-top: 2px; }

    /* Competitor table */
    .comp-row {
        background: #0d1b3e;
        border: 1px solid #1a2a4a;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.4rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .comp-name { color: #c8d8f0; font-weight: 600; }
    .comp-pos  { color: #6a8ab5; font-size: 0.88rem; }

    /* Sigma opportunity cards */
    .opp-card {
        background: #0a0f1e;
        border: 1px solid #1a2a4a;
        border-radius: 14px;
        padding: 1.5rem 1.5rem 1.5rem 0;
        margin-bottom: 1.2rem;
        display: flex;
        gap: 0;
    }
    .opp-number {
        font-family: 'Fraunces', serif;
        font-size: 2.8rem;
        color: #1a3a6e;
        min-width: 80px;
        text-align: center;
        padding-top: 0.2rem;
    }
    .opp-body { flex: 1; }
    .opp-evidence-label { color: #4a6a9a; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
    .opp-evidence { color: #8aa0c8; font-size: 0.9rem; margin: 0.2rem 0 0.8rem 0; }
    .opp-gap-label { color: #8a4a4a; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
    .opp-gap { color: #c89090; font-size: 0.9rem; margin: 0.2rem 0 0.8rem 0; }
    .opp-solution {
        background: #061a0e;
        border-left: 3px solid #00c853;
        border-radius: 0 8px 8px 0;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
    }
    .opp-solution-label { color: #00c853; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
    .opp-solution-text { color: #b0d8b8; font-size: 0.9rem; margin: 0.2rem 0 0 0; }
    .opp-tag {
        display: inline-block;
        background: #0d2a4e;
        color: #5a9af0;
        border-radius: 20px;
        padding: 0.2rem 0.8rem;
        font-size: 0.78rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    /* Alert / callout */
    .callout-warning {
        background: #1a0e00;
        border: 1px solid #7a4a00;
        border-left: 4px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        color: #f0c060;
        font-size: 0.95rem;
    }

    /* Page nav */
    div[data-testid="stRadio"] > div { flex-direction: row; gap: 0.5rem; }
    div[data-testid="stRadio"] label {
        background: #0d1b3e;
        border: 1px solid #1a2a4a;
        border-radius: 20px;
        padding: 0.3rem 0.9rem;
        color: #8aa0c8;
        font-size: 0.88rem;
        cursor: pointer;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background: #0051BA;
        border-color: #0051BA;
        color: #fff;
    }
    .stMetric { background: #0d1b3e; border: 1px solid #1a2a4a; border-radius: 10px; padding: 0.8rem 1rem; }
    .stMetric label { color: #6a8ab5 !important; font-size: 0.8rem !important; }
    .stMetric [data-testid="stMetricValue"] { color: #e0eaff !important; font-size: 1.6rem !important; }
    hr { border-color: #1a2a4a; }
    .stInfo { background: #051428; border-color: #0a3060; color: #8ab0e0; }
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
        return pd.DataFrame(data)
    except Exception as e:
        st.warning(f"Twitter API: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def fetch_youtube_data(query, api_key, max_results=20):
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        search = youtube.search().list(q=query, part="id,snippet", type="video", maxResults=max_results, order="viewCount").execute()
        videos, comments = [], []
        for item in search.get("items", []):
            vid = item["id"]["videoId"]
            stats_r = youtube.videos().list(part="statistics,snippet", id=vid).execute()
            if stats_r["items"]:
                s = stats_r["items"][0]["statistics"]
                sn = stats_r["items"][0]["snippet"]
                videos.append({
                    "video_id": vid,
                    "title": sn["title"],
                    "published_at": sn["publishedAt"],
                    "view_count": int(s.get("viewCount", 0)),
                    "like_count": int(s.get("likeCount", 0)),
                    "comment_count": int(s.get("commentCount", 0)),
                    "channel": sn.get("channelTitle", ""),
                })
                try:
                    cr = youtube.commentThreads().list(part="snippet", videoId=vid, maxResults=20).execute()
                    for ci in cr.get("items", []):
                        c = ci["snippet"]["topLevelComment"]["snippet"]
                        comments.append({
                            "video_id": vid,
                            "comment": c["textDisplay"],
                            "like_count": c["likeCount"],
                            "published_at": c["publishedAt"],
                        })
                except Exception:
                    pass
        return pd.DataFrame(videos), pd.DataFrame(comments)
    except Exception as e:
        st.warning(f"YouTube API: {e}")
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
            data = r.json()
            for post in data.get("data", {}).get("children", []):
                p = post["data"]
                all_posts.append({
                    "title": p.get("title"),
                    "selftext": p.get("selftext", ""),
                    "score": p.get("score"),
                    "num_comments": p.get("num_comments"),
                    "created_utc": p.get("created_utc"),
                    "subreddit": p.get("subreddit"),
                    "url": "https://reddit.com" + p.get("permalink", ""),
                    "upvote_ratio": p.get("upvote_ratio"),
                })
        except Exception as e:
            st.warning(f"Reddit fetch error for r/{sub}: {e}")
    return pd.DataFrame(all_posts)


@st.cache_data(ttl=3600)
def fetch_news(query, api_key, days_back=30):
    try:
        from newsapi import NewsApiClient
        newsapi = NewsApiClient(api_key=api_key)
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        results = newsapi.get_everything(q=query, from_param=from_date, language="en", sort_by="publishedAt", page_size=50)
        articles = results.get("articles", [])
        return pd.DataFrame([{
            "title": a["title"],
            "source": a["source"]["name"],
            "published_at": a["publishedAt"],
            "url": a["url"],
            "description": a.get("description", ""),
        } for a in articles if a.get("title")])
    except Exception as e:
        st.warning(f"News API: {e}")
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
  <h1>💳 Vera Credit · Social Intelligence Dashboard</h1>
  <p>Sigma AI Analytics &nbsp;·&nbsp; Pre-Call Preparation &nbsp;·&nbsp; June 2026</p>
</div>
""", unsafe_allow_html=True)

page = st.radio(
    "",
    ["🏠 Brand Snapshot", "🐦 Twitter / X", "📺 YouTube", "📸 Instagram", "📘 Facebook", "💬 Reddit", "📰 News", "📊 Sigma Opportunity"],
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("---")

# ============================================
# PAGE 1 — BRAND SNAPSHOT
# ============================================
if page == "🏠 Brand Snapshot":
    st.info("**What this page is telling you:** Vera is a brand-new, invite-only credit card with a differentiated product and an experienced CEO — but zero measurable social or data infrastructure. The competitive landscape is well-established. The window to own brand voice is now.")

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
        color_continuous_scale="Blues",
        title="Competitive Positioning: Near-Prime Focus vs. Rewards Flexibility (bubble = brand awareness)",
        template="plotly_dark",
    )
    fig.update_traces(textposition="top center")
    fig.update_layout(height=480, paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e")
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Vera's product is uniquely positioned on rewards flexibility and digital-first — but its market awareness (bubble size) is near zero. That gap is the opportunity.")


# ============================================
# PAGE 2 — TWITTER / X
# ============================================
elif page == "🐦 Twitter / X":
    st.info("**What this page is telling you:** Vera has essentially zero Twitter presence. Competitors are generating thousands of mentions per week from Vera's exact target customers. This is both a risk and a concrete, fixable opportunity.")

    if not TWITTER_BEARER_TOKEN:
        st.error("Add TWITTER_BEARER_TOKEN to Streamlit secrets.")
        st.stop()

    with st.spinner("Fetching Twitter data…"):
        vera_dfs = []
        for q in TWITTER_VERA_QUERIES:
            df = fetch_twitter_data(q, TWITTER_BEARER_TOKEN, max_results=100)
            vera_dfs.append(df)
        vera_tw = pd.concat(vera_dfs, ignore_index=True).drop_duplicates(subset=["text"]) if any(not d.empty for d in vera_dfs) else pd.DataFrame()

        comp_tw = {}
        for name, q in TWITTER_COMPETITOR_QUERIES.items():
            comp_tw[name] = fetch_twitter_data(q, TWITTER_BEARER_TOKEN, max_results=100)

    # Metrics
    vera_count = len(vera_tw)
    comp_counts = {n: len(df) for n, df in comp_tw.items()}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Vera Mentions (7d)", f"{vera_count:,}")
    with col2:
        top_comp = max(comp_counts, key=comp_counts.get) if comp_counts else "—"
        st.metric(f"Top Competitor ({top_comp})", f"{comp_counts.get(top_comp, 0):,}")
    with col3:
        if not vera_tw.empty:
            vera_tw["sentiment"] = vera_tw["text"].apply(score_sentiment)
            pos_pct = (vera_tw["sentiment"] == "Positive").mean() * 100
            st.metric("Vera Positive Sentiment", f"{pos_pct:.0f}%")
        else:
            st.metric("Vera Positive Sentiment", "N/A")
    with col4:
        total_comp = sum(comp_counts.values())
        ratio = f"1 : {total_comp // vera_count}" if vera_count > 0 else "∞"
        st.metric("Vera vs All Competitors", ratio)

    if vera_count < 5:
        empty_vera_warning()

    st.markdown("---")

    # Side-by-side mention bar chart
    all_brands = {"Vera": vera_count, **comp_counts}
    bar_df = pd.DataFrame({"Brand": list(all_brands.keys()), "Mentions": list(all_brands.values())})
    bar_df["Color"] = bar_df["Brand"].apply(lambda x: "#0051BA" if x == "Vera" else "#374151")
    fig_bar = go.Figure(go.Bar(
        x=bar_df["Brand"],
        y=bar_df["Mentions"],
        marker_color=bar_df["Color"],
        text=bar_df["Mentions"],
        textposition="outside",
    ))
    fig_bar.update_layout(
        title="Twitter Mentions (Last 7 Days): Vera vs Competitors",
        template="plotly_dark", paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
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
                          hole=0.4, template="plotly_dark")
        fig_sent.update_layout(paper_bgcolor="#0a0f1e", height=340)
        st.plotly_chart(fig_sent, use_container_width=True)

    # Timeline
    if not vera_tw.empty and "created_at" in vera_tw.columns:
        vera_tw["date"] = pd.to_datetime(vera_tw["created_at"]).dt.date
        daily = vera_tw.groupby("date").size().reset_index(name="mentions")
        fig_line = px.line(daily, x="date", y="mentions", markers=True,
                           title="Vera Mention Volume Over Time",
                           template="plotly_dark")
        fig_line.update_traces(line_color="#0051BA")
        fig_line.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e", height=320)
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
    st.info("**What this page is telling you:** Vera has zero YouTube presence. The competitor review ecosystem generates 50k–500k view videos. These viewers are Vera's exact target customers, actively researching credit cards at the moment of decision — and Vera is invisible to them.")

    if not YOUTUBE_API_KEY:
        st.error("Add YOUTUBE_API_KEY to Streamlit secrets.")
        st.stop()

    with st.spinner("Fetching YouTube data…"):
        vera_vid_dfs = []
        for q in YOUTUBE_VERA_QUERIES:
            vdf, _ = fetch_youtube_data(q, YOUTUBE_API_KEY, max_results=10)
            vera_vid_dfs.append(vdf)
        vera_vids = pd.concat(vera_vid_dfs, ignore_index=True).drop_duplicates(subset=["video_id"]) if any(not d.empty for d in vera_vid_dfs) else pd.DataFrame()

        comp_vids = {}
        comp_comments = {}
        for name, q in YOUTUBE_COMPETITOR_QUERIES.items():
            vdf, cdf = fetch_youtube_data(q, YOUTUBE_API_KEY, max_results=15)
            comp_vids[name] = vdf
            comp_comments[name] = cdf

    vera_vid_count = len(vera_vids)
    vera_views = vera_vids["view_count"].sum() if not vera_vids.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Vera Videos Found", f"{vera_vid_count:,}")
    with col2:
        st.metric("Total Vera Views", f"{vera_views:,}")
    with col3:
        top_comp_vids = max(comp_vids, key=lambda n: len(comp_vids[n])) if comp_vids else "—"
        st.metric(f"Competitor Videos ({top_comp_vids})", f"{len(comp_vids.get(top_comp_vids, [])):,}")
    with col4:
        total_comp_views = sum(df["view_count"].sum() for df in comp_vids.values() if not df.empty)
        st.metric("Total Competitor Views", f"{total_comp_views:,}")

    if vera_vid_count < 5:
        empty_vera_warning()

    st.markdown("---")

    # Vera vs competitor video count
    vid_compare = {"Vera": vera_vid_count}
    for n, df in comp_vids.items():
        vid_compare[n] = len(df)
    vc_df = pd.DataFrame({"Brand": list(vid_compare.keys()), "Videos": list(vid_compare.values())})
    vc_df["Color"] = vc_df["Brand"].apply(lambda x: "#0051BA" if x == "Vera" else "#374151")
    fig_vc = go.Figure(go.Bar(x=vc_df["Brand"], y=vc_df["Videos"],
                               marker_color=vc_df["Color"], text=vc_df["Videos"], textposition="outside"))
    fig_vc.update_layout(title="YouTube Video Count: Vera vs Competitors",
                         template="plotly_dark", paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                         height=360, showlegend=False)
    st.plotly_chart(fig_vc, use_container_width=True)
    st.caption("Every competitor video is a touchpoint where a potential Vera customer is being influenced — without Vera in the room.")

    # View count comparison
    view_compare = {"Vera": vera_views}
    for n, df in comp_vids.items():
        view_compare[n] = int(df["view_count"].sum()) if not df.empty else 0
    vw_df = pd.DataFrame({"Brand": list(view_compare.keys()), "Views": list(view_compare.values())})
    vw_df["Color"] = vw_df["Brand"].apply(lambda x: "#0051BA" if x == "Vera" else "#374151")
    fig_vw = go.Figure(go.Bar(x=vw_df["Brand"], y=vw_df["Views"],
                               marker_color=vw_df["Color"], text=vw_df["Views"], textposition="outside"))
    fig_vw.update_layout(title="Total YouTube Views: Vera vs Competitors",
                         template="plotly_dark", paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
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
    st.info("**What this page is telling you:** Hundreds of posts per month from Vera's exact target customers, on the exact subreddits Vera should be engaging with, discussing the precise problems Vera solves. Vera is not mentioned in any of them.")

    with st.spinner("Fetching Reddit data (no API key needed)…"):
        vera_reddit_dfs = []
        for term in REDDIT_VERA_TERMS:
            df = fetch_reddit_data(term, SUBREDDITS, limit=50)
            vera_reddit_dfs.append(df)
        vera_reddit = pd.concat(vera_reddit_dfs, ignore_index=True).drop_duplicates() if any(not d.empty for d in vera_reddit_dfs) else pd.DataFrame()

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
        fig_heat = px.imshow(heat_pivot, color_continuous_scale="Blues",
                             title="Topic Conversation Heatmap — Subreddits Vera Should Own",
                             template="plotly_dark")
        fig_heat.update_layout(paper_bgcolor="#0a0f1e", height=400)
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption("Each cell is a concentration of Vera's target customers discussing the problems Vera solves. Vera has zero posts in any of these communities.")

    # Topic volume bar
    st.markdown("### Topic Post Volume — Vera's Audience Conversations")
    topic_bar_df = pd.DataFrame({"Topic": list(topic_totals.keys()), "Posts": list(topic_totals.values())})
    fig_topic = px.bar(topic_bar_df, x="Posts", y="Topic", orientation="h",
                       color="Posts", color_continuous_scale="Blues",
                       template="plotly_dark",
                       title="Monthly Reddit Posts on Vera's Core Topics")
    fig_topic.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e", height=380, showlegend=False)
    st.plotly_chart(fig_topic, use_container_width=True)
    st.caption("These conversations are happening right now. Vera is not part of any of them. This is a specific, actionable gap Sigma can help close with an audience intelligence model.")

    # Top upvoted topic posts
    all_topic = pd.concat([df for df in topic_dfs.values() if not df.empty], ignore_index=True)
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
    st.info("**What this page is telling you:** Vera has had one significant press hit. Competitors receive ongoing editorial coverage in the exact publications Vera's customers read at the moment of intent. No content strategy = invisible when it matters most.")

    if not NEWS_API_KEY:
        st.warning("NEWS_API_KEY not set. Add it to Streamlit secrets (newsapi.org free tier).")
        st.markdown("**Without live data, here is what we know from public sources:**")
        st.markdown("- Vera's only significant press hit: FinWise Bank / Vera credit card announcement (April 2026)")
        st.markdown("- Petal, Apple Card, Upgrade: covered monthly in NerdWallet, The Points Guy, Forbes, TechCrunch")
        st.markdown("- Vera: no editorial coverage, no review ecosystem, no presence in 'best credit cards' roundups")
        st.stop()

    with st.spinner("Fetching news data…"):
        vera_news_dfs = []
        for q in NEWS_VERA_QUERIES:
            df = fetch_news(q, NEWS_API_KEY)
            vera_news_dfs.append(df)
        vera_news = pd.concat(vera_news_dfs, ignore_index=True).drop_duplicates(subset=["title"]) if any(not d.empty for d in vera_news_dfs) else pd.DataFrame()

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

    if vera_news_count < 5:
        empty_vera_warning()

    # Coverage comparison
    all_brands_news = {"Vera": vera_news_count, **comp_news_counts}
    news_df = pd.DataFrame({"Brand": list(all_brands_news.keys()), "Articles": list(all_brands_news.values())})
    news_df["Color"] = news_df["Brand"].apply(lambda x: "#0051BA" if x == "Vera" else "#374151")
    fig_news = go.Figure(go.Bar(x=news_df["Brand"], y=news_df["Articles"],
                                 marker_color=news_df["Color"], text=news_df["Articles"], textposition="outside"))
    fig_news.update_layout(title="Press Coverage (30 days): Vera vs Competitors",
                           template="plotly_dark", paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
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
                         color="Articles", color_continuous_scale="Blues", template="plotly_dark",
                         title="Vera Press Articles by Source")
        fig_src.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e", height=400, showlegend=False)
        st.plotly_chart(fig_src, use_container_width=True)

        st.markdown("### Vera Articles")
        for _, row in vera_news.head(10).iterrows():
            st.markdown(f"- **[{row['title']}]({row['url']})** — {row['source']} · {str(row['published_at'])[:10]}")

    # Competitor coverage
    all_comp_news = pd.concat([df.assign(brand=n) for n, df in comp_news.items() if not df.empty], ignore_index=True)
    if not all_comp_news.empty:
        st.markdown("### Competitor Coverage — What Vera's Customers Are Reading Instead")
        top_comp_articles = all_comp_news.nlargest(10, "published_at")[["title", "brand", "source", "published_at", "url"]]
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
                              template="plotly_dark", paper_bgcolor="#0a0f1e",
                              plot_bgcolor="#0a0f1e", height=360, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = go.Figure(go.Bar(
                x=static_data["Brand"], y=static_data["Followers (approx)"],
                marker_color=["#374151"] * 4 + ["#0051BA"],
                text=static_data["Followers (approx)"], textposition="outside",
            ))
            fig2.update_layout(title="Instagram Followers — Competitor Accounts (Approx.)",
                               template="plotly_dark", paper_bgcolor="#0a0f1e",
                               plot_bgcolor="#0a0f1e", height=360, showlegend=False)
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
        ig_bar["Color"] = ig_bar["Brand"].apply(lambda x: "#0051BA" if x == "Vera" else "#374151")
        fig_ig = go.Figure(go.Bar(x=ig_bar["Brand"], y=ig_bar["Posts"],
                                   marker_color=ig_bar["Color"], text=ig_bar["Posts"], textposition="outside"))
        fig_ig.update_layout(title="Instagram Hashtag Posts (Recent): Vera vs Competitors",
                              template="plotly_dark", paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                              height=360, showlegend=False)
        st.plotly_chart(fig_ig, use_container_width=True)
        st.caption("Each competitor post is a consumer recommendation or review reaching thousands of Vera's potential customers — without Vera in the conversation.")

        # Topic hashtag volume
        topic_counts = {t: len(df) for t, df in topic_ig.items()}
        topic_df = pd.DataFrame({"Hashtag": [f"#{t}" for t in topic_counts.keys()],
                                  "Posts": list(topic_counts.values())})
        fig_topic = px.bar(topic_df, x="Posts", y="Hashtag", orientation="h",
                           color="Posts", color_continuous_scale="Blues", template="plotly_dark",
                           title="Topic Hashtag Volume — Vera's Audience Conversations on Instagram")
        fig_topic.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e", height=360, showlegend=False)
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
                              template="plotly_dark", paper_bgcolor="#0a0f1e",
                              plot_bgcolor="#0a0f1e", height=360, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = go.Figure(go.Bar(
                x=static_fb["Brand"], y=static_fb["Avg. Post Engagement"],
                marker_color=["#374151"] * 4 + ["#0051BA"],
                text=static_fb["Avg. Post Engagement"], textposition="outside",
            ))
            fig2.update_layout(title="Avg. Post Engagement per Post (Approx.)",
                               template="plotly_dark", paper_bgcolor="#0a0f1e",
                               plot_bgcolor="#0a0f1e", height=360, showlegend=False)
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
        fan_df["Color"] = fan_df["Brand"].apply(lambda x: "#0051BA" if x == "Vera" else "#374151")
        fig_fan = go.Figure(go.Bar(x=fan_df["Brand"], y=fan_df["Followers"],
                                    marker_color=fan_df["Color"], text=fan_df["Followers"], textposition="outside"))
        fig_fan.update_layout(title="Facebook Page Followers: Vera vs Competitors",
                               template="plotly_dark", paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e",
                               height=360, showlegend=False)
        st.plotly_chart(fig_fan, use_container_width=True)
        st.caption("Vera has no Facebook Page. Every competitor follower is a potential Vera customer being nurtured by the competition.")

        # Talking about count
        talking_data = {n: m.get("talking_about", 0) for n, m in comp_fb_meta.items() if m}
        if any(v > 0 for v in talking_data.values()):
            talk_df = pd.DataFrame({"Brand": list(talking_data.keys()), "Talking About (7d)": list(talking_data.values())})
            fig_talk = px.bar(talk_df, x="Brand", y="Talking About (7d)",
                              color="Talking About (7d)", color_continuous_scale="Reds",
                              template="plotly_dark",
                              title="'Talking About' Count — Active Audience Engagement This Week")
            fig_talk.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e", height=340, showlegend=False)
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
                             color="Avg Engagement per Post", color_continuous_scale="Blues",
                             template="plotly_dark", title="Average Post Engagement by Competitor")
            fig_eng.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e", height=340, showlegend=False)
            st.plotly_chart(fig_eng, use_container_width=True)

            # Sentiment on competitor posts
            all_comp_fb["sentiment"] = all_comp_fb["message"].apply(score_sentiment)
            sent_breakdown = all_comp_fb.groupby(["brand", "sentiment"]).size().reset_index(name="count")
            fig_sent = px.bar(sent_breakdown, x="brand", y="count", color="sentiment",
                              color_discrete_map={"Positive": "#00c853", "Neutral": "#5a7ab5", "Negative": "#e53935"},
                              template="plotly_dark", barmode="stack",
                              title="Competitor Post Sentiment — What Emotions Are Driving Engagement?")
            fig_sent.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e", height=360)
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
    st.info("**What this page is telling you:** The data from every previous page points to a specific, measurable set of gaps. Each gap maps directly to a Sigma AI capability. This is the evidence-based case for engagement.")

    st.markdown("""
    <div style="background:#0a0f1e; border:1px solid #1a2a4a; border-radius:14px; padding:1.5rem 2rem; margin-bottom:1.5rem;">
      <div style="font-family: 'Fraunces', serif; color:#5a9af0; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.1em;">The Thesis</div>
      <div style="color:#e0eaff; font-size:1.15rem; margin-top:0.5rem; line-height:1.6;">
        Vera has a differentiated product, an experienced team, and a well-defined target market.
        What it lacks is the <strong style="color:#5a9af0;">measurement infrastructure and analytical models</strong>
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
                     color="Count", color_continuous_scale="Blues", template="plotly_dark",
                     title="Sigma Capabilities Required to Close Vera's Gaps")
    fig_svc.update_layout(paper_bgcolor="#0a0f1e", plot_bgcolor="#0a0f1e", height=320, showlegend=False)
    st.plotly_chart(fig_svc, use_container_width=True)

    # What we are NOT proposing
    st.markdown("""
    <div style="background:#0a0f1e; border:1px solid #1a2a4a; border-radius:14px; padding:1.5rem 2rem; margin-top:1.5rem;">
      <div style="font-family: 'Fraunces', serif; color:#f59e0b; font-size:1.1rem; margin-bottom:0.8rem;">What Sigma is NOT proposing</div>
      <ul style="color:#8aa0c8; line-height:2;">
        <li>We are <strong style="color:#e0eaff;">not</strong> proposing to run Vera's social media.</li>
        <li>We are <strong style="color:#e0eaff;">not</strong> a marketing agency.</li>
        <li>We <strong style="color:#e0eaff;">build the measurement infrastructure and analytical models</strong>
            that tell Vera what is working and what is not — so the Vera team can make faster,
            better decisions with less wasted spend.</li>
        <li>We work as Vera's <strong style="color:#e0eaff;">embedded data science team</strong>,
            not a hands-off vendor.</li>
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
