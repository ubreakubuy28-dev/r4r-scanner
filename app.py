import streamlit as st
import feedparser
import re
import pandas as pd
from datetime import datetime

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="R4R Scanner v3", layout="wide")

# ==========================================
# 2. FILTERING LOGIC
# ==========================================
st.sidebar.header("1. Target Demographics")

# Gender & Age
target_genders = st.sidebar.multiselect(
    "Target Tags",
    ['F4M', 'F4R', 'F4F', 'M4F', 'M4R', 'M4M'],
    default=['F4M']
)
min_age, max_age = st.sidebar.slider("Age Range", 18, 99, (21, 35))

st.sidebar.divider()
st.sidebar.header("2. Content Filters")

# --- INCLUDE FILTER ---
st.sidebar.subheader("✅ MUST Contain (Include)")
enable_include = st.sidebar.checkbox("Enable 'Must Contain'", value=False)
include_text = st.sidebar.text_area(
    "Keywords to find (comma separated)", 
    "asian, latina, nurse, gamer, gym, local, nyc",
    height=60,
    help="The post MUST contain at least one of these words."
)
include_keywords = [k.strip().lower() for k in include_text.split(",") if k.strip()]

# --- EXCLUDE FILTER ---
st.sidebar.subheader("❌ MUST NOT Contain (Exclude)")
enable_exclude = st.sidebar.checkbox("Enable 'Block List'", value=True)
exclude_text = st.sidebar.text_area(
    "Keywords to block (comma separated)", 
    "onlyfans, fansly, selling, seller, buy, $",
    height=60,
    help="If the post contains ANY of these, it will be hidden."
)
exclude_keywords = [k.strip().lower() for k in exclude_text.split(",") if k.strip()]

# --- COMMON PRESETS ---
st.sidebar.subheader("⚡ Quick Blockers")
block_sellers = st.sidebar.checkbox("Block Sellers/Content (OF, Fansly)", value=True)
block_socials = st.sidebar.checkbox("Block Social Spam (Insta, Snap)", value=False)
block_crypto  = st.sidebar.checkbox("Block Crypto/Telegram Spam", value=True)

# Define preset lists
SELLER_TERMS = ["onlyfans", "fansly", "content", "selling", "promo", "sub", "sale", "menu"]
SOCIAL_TERMS = ["instagram", "insta", "ig", "snapchat", "snap", "add me"]
CRYPTO_TERMS = ["crypto", "bitcoin", "telegram", "whatsapp", "invest"]

def parse_entry(entry):
    """Extracts info from an RSS entry."""
    title = entry.title
    content = entry.content[0].value if 'content' in entry else ""
    link = entry.link
    
    # Regex for Age and Tag
    pattern = r"(\d{2})\s*[\[\(]([Ff]4[MmRrFf])[\]\)]"
    match = re.search(pattern, title)
    
    age = int(match.group(1)) if match else None
    tag = match.group(2).upper() if match else None
    
    return {
        "title": title,
        "content": content,
        "full_text": (title + " " + content).lower(),
        "link": link,
        "published": entry.published,
        "age": age,
        "tag": tag,
        "id": entry.id
    }

def passes_filters(post):
    # 1. Basic Metadata Checks
    if not post['age'] or not post['tag']: return False
    if post['tag'] not in target_genders: return False
    if not (min_age <= post['age'] <= max_age): return False
    
    text = post['full_text']

    # 2. Exclude Filter (Custom)
    if enable_exclude:
        if any(bad_word in text for bad_word in exclude_keywords):
            return False

    # 3. Include Filter (Custom)
    if enable_include:
        if not any(good_word in text for good_word in include_keywords):
            return False

    # 4. Quick Blockers (Presets)
    if block_sellers and any(x in text for x in SELLER_TERMS): return False
    if block_socials and any(x in text for x in SOCIAL_TERMS): return False
    if block_crypto and any(x in text for x in CRYPTO_TERMS): return False

    return True

def fetch_rss():
    url = "https://www.reddit.com/r/r4r/new.rss"
    # User-Agent prevents 429/403 errors
    feed = feedparser.parse(url, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    return feed.entries

# ==========================================
# 3. MAIN UI
# ==========================================
st.title("❤️ R4R Scanner v3 (With Block Lists)")

tab1, tab2 = st.tabs(["🔍 Recent Posts", "⚡ Auto-Scan"])

# --- TAB 1: MANUAL SCAN ---
with tab1:
    if st.button("Scan RSS Feed"):
        with st.spinner("Fetching data..."):
            entries = fetch_rss()
            results = []
            
            if not entries:
                st.error("Connection error. Reddit might be blocking this IP temporarily.")
            
            for entry in entries:
                post = parse_entry(entry)
                if passes_filters(post):
                    results.append(post)
            
            if results:
                st.success(f"Found {len(results)} matches!")
                for row in results:
                    # Color code the expander
                    with st.expander(f"[{row['tag']}] {row['age']} - {row['title']}"):
                        st.write(f"**Posted:** {row['published']}")
                        st.markdown(f"[View Post]({row['link']})")
                        st.text("Preview:")
                        st.caption(row['content'][:300] + "...")
            else:
                st.info("No matches found. Try relaxing your filters.")

# --- TAB 2: AUTO SCAN ---
with tab2:
    st.write("Click below to check for NEW posts.")
    if st.button("Check Now"):
        entries = fetch_rss()
        count = 0
        for entry in entries:
            post = parse_entry(entry)
            if passes_filters(post):
                st.markdown(f"**{post['tag']} {post['age']}** | [{post['title']}]({post['link']})")
                count += 1
        if count == 0:
            st.warning("No new matching posts found right now.")
