import streamlit as st
import feedparser
import re
from datetime import datetime

# ==========================================
# 1. SETUP & CONFIG
# ==========================================
st.set_page_config(page_title="R4R Master Scanner", layout="wide")

st.sidebar.title("⚙️ Scanner Settings")

# --- SECTION A: DEMOGRAPHICS ---
st.sidebar.header("1. Target")
target_genders = st.sidebar.multiselect("Gender Tags", ['F4M', 'F4R', 'F4F', 'M4F'], default=['F4M'])
min_age, max_age = st.sidebar.slider("Age Range", 18, 99, (21, 35))

st.sidebar.divider()

# --- SECTION B: CONTENT FILTERS (RESTORED) ---
st.sidebar.header("2. Filtering Rules")

# Exclude (Block)
enable_exclude = st.sidebar.checkbox("⛔ Enable Block List", value=True)
exclude_text = st.sidebar.text_area(
    "Block words (comma separated)", 
    "smoke, 420, poly, married, couple",
    height=60,
    help="Hide posts containing these words."
)
exclude_keywords = [k.strip().lower() for k in exclude_text.split(",") if k.strip()]

# Include (Must Have)
enable_include = st.sidebar.checkbox("✅ Enable 'Must Have'", value=False)
include_text = st.sidebar.text_area(
    "Must contain (comma separated)", 
    "local, nyc, gamer, nurse, gym",
    height=60,
    help="Only show posts that have at least one of these."
)
include_keywords = [k.strip().lower() for k in include_text.split(",") if k.strip()]

# Quick Blockers
st.sidebar.subheader("⚡ Quick Blocks")
block_sellers = st.sidebar.checkbox("Block Sellers (OF/Fansly)", value=True)
block_crypto  = st.sidebar.checkbox("Block Crypto/Spam", value=True)

# Preset Lists
SELLER_TERMS = ["onlyfans", "fansly", "selling", "promo", "prices", "cashapp", "paypal", "menu"]
CRYPTO_TERMS = ["crypto", "bitcoin", "telegram", "whatsapp", "invest"]

st.sidebar.divider()

# --- SECTION C: YOUR PERSONA (FOR REPLIES) ---
st.sidebar.header("3. Reply Assistant")
my_interests = st.sidebar.text_area("Your Hobbies (for drafts)", "tennis and video games")
my_name = st.sidebar.text_input("Your Sign-off Name", "Me")

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def contains_word(text, word_list):
    """Checks for whole words to avoid false positives (e.g. 'sub' in 'subject')."""
    # Normalize text: lowercase and pad with spaces
    clean_text = " " + re.sub(r'[^\w\s]', '', text).lower() + " "
    for word in word_list:
        if f" {word} " in clean_text:
            return True
    return False

def generate_reply_data(post):
    """Generates the draft text and the Chat URL."""
    author_clean = post['author'].replace('/u/', '').replace('u/', '').strip()
    full_text = post['full_text']
    
    # Simple Interest Matching
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
    # 1. Demographics
    if not post['age'] or not post['tag']: return False
    if post['tag'] not in target_genders: return False
    if not (min_age <= post['age'] <= max_age): return False
    
    text = post['full_text']

    # 2. Block List (User Defined)
    if enable_exclude and contains_word(text, exclude_keywords):
        return False

    # 3. Must Have List (User Defined)
    if enable_include and not contains_word(text, include_keywords):
        return False

    # 4. Quick Blockers (Presets)
    if block_sellers and contains_word(text, SELLER_TERMS): return False
    if block_crypto and contains_word(text, CRYPTO_TERMS): return False
            
    return True

def fetch_rss():
    url = "https://www.reddit.com/r/r4r/new.rss"
    return feedparser.parse(url, agent="Mozilla/5.0").entries

# ==========================================
# 3. MAIN UI
# ==========================================
st.title("🚀 R4R Master Scanner")

tab1, tab2 = st.tabs(["🔍 Live Scanner", "ℹ️ How to Use"])

with tab1:
    if st.button("🔄 Scan Feed"):
        entries = fetch_rss()
        count = 0
        
        # Determine layout columns once
        
        for entry in entries:
            post = parse_entry(entry)
            
            # Apply ALL filters (Demographic + Block + Include)
            if passes_filters(post):
                count += 1
                chat_link, draft_text, username = generate_reply_data(post)
                
                # Render the Result
                with st.expander(f"[{post['tag']}] {post['age']} | {post['title']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**User:** {username} | **Posted:** {post['published']}")
                        st.info(post['content'][:500] + "...") # Show more text
                        st.markdown(f"[🔗 View Original Post]({post['link']})")
                    
                    with col2:
                        st.write("### 👇 Action")
                        st.text_area("Draft (Ctrl+C)", draft_text, height=130, key=post['link'])
                        st.markdown(
                            f"""<a href="{chat_link}" target="_blank"><button style="background-color:#0079D3; color:white; padding:10px; border-radius:5px; width:100%; border:none;">💬 Chat with {username}</button></a>""", 
                            unsafe_allow_html=True
                        )
        
        if count == 0:
            st.warning("No matches found. Try relaxing your 'Must Have' filters or 'Block List'.")
        else:
            st.success(f"Found {count} matches!")

with tab2:
    st.write("### Instructions")
    st.write("1. **Sidebar:** Set your filters. 'Enable Must Have' is the strictest filter.")
    st.write("2. **Scan:** Click the button in the Live Scanner tab.")
    st.write("3. **Reply:** Copy the text from the draft box, click the Chat button, paste, and send.")
