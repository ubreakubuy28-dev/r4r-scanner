import streamlit as st
import feedparser
import re
import pandas as pd
from datetime import datetime
import time

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="R4R RSS Scanner", layout="wide")

# ==========================================
# 2. FILTERING LOGIC
# ==========================================
st.sidebar.header("Search Filters")

target_genders = st.sidebar.multiselect(
    "Target Gender Tags",
    ['F4M', 'F4R', 'F4F', 'M4F', 'M4R', 'M4M'],
    default=['F4M']
)

min_age, max_age = st.sidebar.slider("Age Range", 18, 99, (21, 35))

st.sidebar.subheader("Keyword/Ethnicity Filter")
enable_keyword_filter = st.sidebar.checkbox("Enable Keyword Filter")
keywords_input = st.sidebar.text_area(
    "Keywords", 
    "asian, latina, white, black, korean, japanese, hispanic, colombian, filipina",
    height=100
)
keywords = [k.strip().lower() for k in keywords_input.split(",") if k.strip()]

def parse_entry(entry):
    """Extracts info from an RSS entry."""
    title = entry.title
    # RSS content is HTML, we strip it simply for checking
    content = entry.content[0].value if 'content' in entry else ""
    link = entry.link
    
    # Pattern: 24 [F4M]
    pattern = r"(\d{2})\s*[\[\(]([Ff]4[MmRrFf])[\]\)]"
    match = re.search(pattern, title)
    
    age = int(match.group(1)) if match else None
    tag = match.group(2).upper() if match else None
    
    return {
        "title": title,
        "content": content,
        "link": link,
        "published": entry.published,
        "age": age,
        "tag": tag,
        "id": entry.id
    }

def passes_filters(post):
    if not post['age'] or not post['tag']: return False
    if post['tag'] not in target_genders: return False
    if not (min_age <= post['age'] <= max_age): return False
    
    if enable_keyword_filter:
        full_text = (post['title'] + " " + post['content']).lower()
        if not any(k in full_text for k in keywords):
            return False
    return True

def fetch_rss():
    # We use the RSS feed which is often less blocked than JSON
    url = "https://www.reddit.com/r/r4r/new.rss"
    # User-Agent is critical
    feed = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    return feed.entries

# ==========================================
# 3. MAIN UI
# ==========================================
st.title("❤️ R4R RSS Scanner (Cloud Fix)")

tab1, tab2 = st.tabs(["🔍 Recent Posts", "⚡ Auto-Scan"])

with tab1:
    if st.button("Scan RSS Feed"):
        with st.spinner("Fetching RSS feed..."):
            entries = fetch_rss()
            results = []
            
            if not entries:
                st.error("Could not fetch data. Reddit might still be blocking this IP.")
            
            for entry in entries:
                post = parse_entry(entry)
                if passes_filters(post):
                    results.append(post)
            
            if results:
                st.success(f"Found {len(results)} matches!")
                for row in results:
                    with st.expander(f"[{row['tag']}] {row['age']} - {row['title']}"):
                        st.write(f"**Posted:** {row['published']}")
                        st.markdown(f"[View Post]({row['link']})")
            else:
                st.info("No matches in the current RSS feed.")

with tab2:
    st.write("Checks for new items every time you click.")
    if st.button("Check Now"):
        entries = fetch_rss()
        count = 0
        for entry in entries:
            post = parse_entry(entry)
            if passes_filters(post):
                st.markdown(f"**{post['tag']} {post['age']}** | [{post['title']}]({post['link']})")
                count += 1
        if count == 0:
            st.warning("No matches found.")
