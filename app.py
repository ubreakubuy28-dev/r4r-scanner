import streamlit as st
import requests
import re
import pandas as pd
from datetime import datetime
import time

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
st.set_page_config(page_title="R4R Partner Finder (No-Login)", layout="wide")

# Custom headers are REQUIRED so Reddit doesn't block the script
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# ==========================================
# 2. FILTERING LOGIC
# ==========================================
st.sidebar.header("Search Filters")

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

def parse_post_data(post_data):
    """Extracts relevant info from raw JSON data."""
    title = post_data.get('title', '')
    selftext = post_data.get('selftext', '')
    url = post_data.get('url', '')
    created_utc = post_data.get('created_utc', 0)
    
    # Pattern covers: 24 [F4M], (24) [f4m], [f4m] 24
    pattern = r"(\d{2})\s*[\[\(]([Ff]4[MmRrFf])[\]\)]"
    match = re.search(pattern, title)
    
    age = int(match.group(1)) if match else None
    tag = match.group(2).upper() if match else None
    
    return {
        "title": title,
        "selftext": selftext,
        "url": url,
        "created_utc": created_utc,
        "age": age,
        "tag": tag,
        "id": post_data.get('id')
    }

def passes_filters(post):
    if not post['age'] or not post['tag']:
        return False
    
    if post['tag'] not in target_genders:
        return False
        
    if not (min_age <= post['age'] <= max_age):
        return False
    
    if enable_keyword_filter:
        full_text = (post['title'] + " " + post['selftext']).lower()
        if not any(k in full_text for k in keywords):
            return False
            
    return True

def fetch_reddit_json(sort="new", limit=25):
    """Fetches public JSON data from Reddit without API keys."""
    url = f"https://www.reddit.com/r/r4r/{sort}.json?limit={limit}"
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            return data['data']['children'] # This is the list of posts
        elif response.status_code == 429:
            st.error("Rate limit hit! Reddit is asking us to slow down. Wait a moment.")
            return []
        else:
            st.error(f"Error fetching data: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Connection error: {e}")
        return []

# ==========================================
# 3. MAIN APP INTERFACE
# ==========================================
st.title("❤️ R4R Intelligent Scanner (No-API Version)")

tab1, tab2 = st.tabs(["🔍 Search Recent", "⚡ Live Scanner"])

# --- TAB 1: HISTORICAL SEARCH ---
with tab1:
    st.write("Scan the most recent posts.")
    if st.button("Scan Now"):
        with st.spinner("Fetching public data..."):
            raw_posts = fetch_reddit_json(sort="new", limit=100)
            results = []
            
            for entry in raw_posts:
                post = parse_post_data(entry['data'])
                if passes_filters(post):
                    results.append({
                        "Posted": datetime.fromtimestamp(post['created_utc']).strftime('%Y-%m-%d %H:%M'),
                        "Tag": post['tag'],
                        "Age": post['age'],
                        "Title": post['title'],
                        "Link": post['url'],
                        "Preview": post['selftext'][:200]
                    })
            
            if results:
                st.success(f"Found {len(results)} matches!")
                for row in results:
                    with st.expander(f"[{row['Tag']}] {row['Age']} - {row['Title']}"):
                        st.write(f"**Posted:** {row['Posted']}")
                        st.write(row["Preview"] + "...")
                        st.markdown(f"[View Post on Reddit]({row['Link']})")
            else:
                st.info("No matches found in the last 100 posts.")

# --- TAB 2: LIVE SCANNER ---
with tab2:
    st.write("This will check the 'New' feed.")
    
    if 'live_data' not in st.session_state:
        st.session_state.live_data = []

    if st.button("Check for New Posts"):
        raw_posts = fetch_reddit_json(sort="new", limit=10)
        found_new = 0
        
        for entry in raw_posts:
            post = parse_post_data(entry['data'])
            
            # Check for duplicates using ID
            if not any(d['id'] == post['id'] for d in st.session_state.live_data):
                if passes_filters(post):
                    st.session_state.live_data.insert(0, {
                        "id": post['id'],
                        "time": datetime.now().strftime('%H:%M'),
                        "title": post['title'],
                        "link": post['url'],
                        "tag": post['tag'],
                        "age": post['age']
                    })
                    found_new += 1
        
        if found_new > 0:
            st.success(f"Found {found_new} new matching posts!")
        else:
            st.info("No new matches found right now.")

    # Display Live Feed
    if st.session_state.live_data:
        for item in st.session_state.live_data:
            st.markdown(f"⏰ **{item['time']}** | **{item['tag']} {item['age']}** | [{item['title']}]({item['link']})")
