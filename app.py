import streamlit as st
import praw
import re
import pandas as pd
from datetime import datetime

# ==========================================
# 1. SETUP & AUTHENTICATION
# ==========================================
st.set_page_config(page_title="R4R Partner Finder", layout="wide")

st.sidebar.header("1. Reddit API Settings")

# Check if keys are stored in Streamlit Secrets (Cloud Hosting)
if "reddit" in st.secrets:
    client_id = st.secrets["reddit"]["client_id"]
    client_secret = st.secrets["reddit"]["client_secret"]
    st.sidebar.success("✅ API Keys loaded from Cloud Secrets")
else:
    # Fallback to manual entry if running locally
    client_id = st.sidebar.text_input("Client ID", type="password")
    client_secret = st.sidebar.text_input("Client Secret", type="password")

user_agent = "web:r4r_finder:v1.0 (by /u/custom_script)"

# Initialize PRAW
if client_id and client_secret:
    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
    except Exception as e:
        st.error(f"Error connecting to Reddit: {e}")
        st.stop()
else:
    st.warning("Please enter credentials to start.")
    st.stop()

# ==========================================
# 2. FILTERING LOGIC
# ==========================================
st.sidebar.header("2. Search Filters")

# Gender Filter
target_genders = st.sidebar.multiselect(
    "Target Gender Tags",
    ['F4M', 'F4R', 'F4F', 'M4F', 'M4R', 'M4M'],
    default=['F4M']
)

# Age Filter
min_age, max_age = st.sidebar.slider("Age Range", 18, 99, (21, 35))

# Keyword Filter
st.sidebar.subheader("Keyword/Ethnicity Filter")
enable_keyword_filter = st.sidebar.checkbox("Enable Keyword Filter")
keywords_input = st.sidebar.text_area(
    "Keywords (comma separated)", 
    "asian, latina, white, black, korean, japanese, hispanic, colombian, filipina",
    height=100
)
keywords = [k.strip().lower() for k in keywords_input.split(",") if k.strip()]

def parse_post(submission):
    """Extracts age and gender tag from title."""
    # Pattern covers: 24 [F4M], (24) [f4m], [f4m] 24
    pattern = r"(\d{2})\s*[\[\(]([Ff]4[MmRrFf])[\]\)]"
    match = re.search(pattern, submission.title)
    if match:
        return int(match.group(1)), match.group(2).upper()
    return None, None

def passes_filters(submission, age, tag):
    if tag not in target_genders: return False
    if not (min_age <= age <= max_age): return False
    
    if enable_keyword_filter:
        full_text = (submission.title + " " + submission.selftext).lower()
        if not any(k in full_text for k in keywords):
            return False
    return True

# ==========================================
# 3. MAIN APP INTERFACE
# ==========================================
st.title("❤️ R4R Intelligent Scanner")

tab1, tab2 = st.tabs(["🔍 Historical Search", "⚡ Live Scanner"])

# --- TAB 1: HISTORICAL SEARCH ---
with tab1:
    st.write("Search past posts (Day/Week/Month).")
    col1, col2 = st.columns(2)
    with col1:
        search_limit = st.slider("Max Posts to Scan", 50, 1000, 100)
    with col2:
        time_filter = st.selectbox("Time Range", ["day", "week", "month", "all"])
    
    if st.button("Run Search"):
        with st.spinner(f"Scanning the last {search_limit} posts..."):
            subreddit = reddit.subreddit("r4r")
            
            # Decide between .new() or .top() based on time filter
            if time_filter == "day":
                posts = subreddit.new(limit=search_limit)
            else:
                posts = subreddit.top(time_filter=time_filter, limit=search_limit)

            results = []
            for post in posts:
                try:
                    age, tag = parse_post(post)
                    if age and passes_filters(post, age, tag):
                        results.append({
                            "Posted": datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M'),
                            "Tag": tag,
                            "Age": age,
                            "Title": post.title,
                            "Link": f"https://reddit.com{post.permalink}",
                            "Preview": post.selftext[:200]
                        })
                except:
                    continue
            
            if results:
                st.success(f"Found {len(results)} matches!")
                for row in results:
                    with st.expander(f"[{row['Tag']}] {row['Age']} - {row['Title']}"):
                        st.write(f"**Posted:** {row['Posted']}")
                        st.write(row["Preview"] + "...")
                        st.markdown(f"[View Post on Reddit]({row['Link']})")
            else:
                st.info("No matches found.")

# --- TAB 2: LIVE SCANNER ---
with tab2:
    st.write("Click below to check for the very latest posts.")
    if st.button("Refresh Feed"):
        subreddit = reddit.subreddit("r4r")
        new_posts = subreddit.new(limit=25)
        
        found = 0
        for post in new_posts:
            age, tag = parse_post(post)
            if age and passes_filters(post, age, tag):
                found += 1
                st.markdown(f"**{tag} {age}** | [{post.title}](https://reddit.com{post.permalink})")
        
        if found == 0:
            st.warning("No matching new posts right now.")