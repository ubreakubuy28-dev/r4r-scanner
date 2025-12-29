import streamlit as st
import feedparser
import re
import urllib.parse
from datetime import datetime

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
st.set_page_config(page_title="R4R Deep Scanner", layout="wide")

st.sidebar.title("⚙️ Scanner Settings")

# --- SECTION A: DEMOGRAPHICS ---
st.sidebar.header("1. Target")
# We use these to build the Reddit Search Query
target_genders = st.sidebar.multiselect("Gender Tags", ['F4M', 'F4R', 'F4F', 'M4F'], default=['F4M'])
min_age, max_age = st.sidebar.slider("Age Range", 18, 99, (21, 35))

st.sidebar.divider()

# --- SECTION B: CONTENT FILTERS ---
st.sidebar.header("2. Filtering Rules")

enable_exclude = st.sidebar.checkbox("⛔ Enable Block List", value=True)
exclude_text = st.sidebar.text_area(
    "Block words (comma separated)", 
    "smoke, 420, poly, married, couple",
    height=60
)
exclude_keywords = [k.strip().lower() for k in exclude_text.split(",") if k.strip()]

enable_include = st.sidebar.checkbox("✅ Enable 'Must Have'", value=False)
include_text = st.sidebar.text_area(
    "Must contain (comma separated)", 
    "local, nyc, gamer, nurse, gym",
    height=60
)
include_keywords = [k.strip().lower() for k in include_text.split(",") if k.strip()]

# Quick Blockers
st.sidebar.subheader("⚡ Quick Blocks")
block_sellers = st.sidebar.checkbox("Block Sellers (OF/Fansly)", value=True)
block_crypto  = st.sidebar.checkbox("Block Crypto/Spam", value=True)

SELLER_TERMS = ["onlyfans", "fansly", "selling", "promo", "prices", "cashapp", "paypal", "menu"]
CRYPTO_TERMS = ["crypto", "bitcoin", "telegram", "whatsapp", "invest"]

st.sidebar.divider()

# --- SECTION C: YOUR PERSONA ---
st.sidebar.header("3. Reply Assistant")
my_interests = st.sidebar.text_area("Your Hobbies", "tennis and video games")
my_name = st.sidebar.text_input("Your Sign-off Name", "Me")

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def contains_word(text, word_list):
    """Checks for whole words to avoid false positives."""
    clean_text = " " + re.sub(r'[^\w\s]', '', text).lower() + " "
    for word in word_list:
        if f" {word} " in clean_text:
            return True
    return False

def generate_reply_data(post):
    author_clean = post['author'].replace('/u/', '').replace('u/', '').strip()
    full_text = post['full_text']
    
    tennis_keywords = ['tennis', 'wta', 'atp', 'racket', 'court', 'sport', 'active', 'gym']
    game_keywords = ['game', 'gaming', 'steam', 'ps5', 'switch', 'pc', 'play', 'discord']
    
    if any(k in full_text for k in tennis_keywords):
        draft = (
            f"Hey! I saw your r4r post and noticed the mention of tennis/sports. "
            f"I'm actually really big into tennis myself. "
            f"I liked what you said about '{post['title'][:30]}...' - felt like we might vibe. "
            f"Would love to chat if you're open to it! -{my_name}"
        )
    elif any(k in full_text for k in game_keywords):
        draft = (
            f"Hey! Saw your post and noticed you're a gamer. "
            f"I play a lot on PC/Console myself (mainly {my_interests}). "
            f"I liked your intro and thought I'd say hi. "
            f"Up for a game or a chat sometime? -{my_name}"
        )
    else:
        draft = (
            f"Hi! I just read your post about '{post['title'][:40]}...' and thought you sounded pretty cool. "
            f"I'm also looking for a genuine connection. I'm mainly into {my_interests}, but always down to chat about whatever. "
            f"Hope your day is going well! -{my_name}"
        )

    chat_link = f"https://www.reddit.com/chat/u/{author_clean}"
    return chat_link, draft, author_clean

def parse_entry(entry):
    title = entry.title
    content = entry.content[0].value if 'content' in entry else ""
    author = entry.get('author', 'Unknown')
    
    pattern = r"(\d{2})\s*[\[\(]([Ff]4[MmRrFf])[\]\)]"
    match = re.search(pattern, title)
    age = int(match.group(1)) if match else None
    tag = match.group(2).upper() if match else None
    
    return {
        "title": title,
        "content": content,
        "full_text": (title + " " + content).lower(),
        "link": entry.link,
        "published": entry.published,
        "age": age,
        "tag": tag,
        "author": author
    }

def passes_filters(post):
    # Note: We don't need to check Gender Tag here because we pre-filtered in the RSS URL!
    if not post['age'] or not post['tag']: return False
    if not (min_age <= post['age'] <= max_age): return False
    
    text = post['full_text']

    if enable_exclude and contains_word(text, exclude_keywords): return False
    if enable_include and not contains_word(text, include_keywords): return False
    if block_sellers and contains_word(text, SELLER_TERMS): return False
    if block_crypto and contains_word(text, CRYPTO_TERMS): return False
            
    return True

def fetch_targeted_rss():
    # 1. Construct a Search Query for the specific Tags
    # This forces Reddit to give us 25 F4M posts, not just 25 random posts.
    if not target_genders:
        query = 'subreddit:r4r' # Fallback
    else:
        # queries usually look like: title:"F4M" OR title:"F4R"
        tags_query = " OR ".join([f'title:"{t}"' for t in target_genders])
        query = f'subreddit:r4r ({tags_query})'

    encoded_query = urllib.parse.quote(query)
    
    # "sort=new" ensures we get the latest ones
    url = f"https://www.reddit.com/r/search.rss?q={encoded_query}&sort=new"
    
    return feedparser.parse(url, agent="Mozilla/5.0").entries

# ==========================================
# 3. MAIN UI
# ==========================================
st.title("🚀 R4R Deep Scanner (24h+)")

tab1, tab2 = st.tabs(["🔍 Deep Search", "ℹ️ Info"])

with tab1:
    if st.button("🔄 Scan Last 25 Matches"):
        with st.spinner("Searching Reddit History..."):
            entries = fetch_targeted_rss()
            count = 0
            
            if not entries:
                st.error("No data received. Reddit might be blocking requests or the search query is empty.")
            
            for entry in entries:
                try:
                    post = parse_entry(entry)
                    if passes_filters(post):
                        count += 1
                        chat_link, draft_text, username = generate_reply_data(post)
                        
                        with st.expander(f"[{post['tag']}] {post['age']} | {post['title']}"):
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.markdown(f"**User:** {username} | **Posted:** {post['published']}")
                                st.info(post['content'][:500] + "...")
                                st.markdown(f"[🔗 View Post]({post['link']})")
                            with col2:
                                st.write("### 👇 Action")
                                st.text_area("Draft", draft_text, height=130, key=post['link'])
                                st.markdown(f"""<a href="{chat_link}" target="_blank"><button style="background-color:#0079D3; color:white; padding:10px; border-radius:5px; width:100%; border:none;">💬 Chat</button></a>""", unsafe_allow_html=True)
                except Exception as e:
                    continue
            
            if count == 0:
                st.warning("No matches found in the last batch. Try disabling 'Must Have' or 'Block List' temporarily.")
            else:
                st.success(f"Found {count} targeted matches!")

with tab2:
    st.write("### Why this finds more posts")
    st.write("Instead of checking the 'New' feed (which is full of spam), this sends a specific Search Query to Reddit for 'F4M' sorted by new.")
    st.write("This usually retrieves posts from the last 12-24 hours.")
