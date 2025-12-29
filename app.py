import streamlit as st
import requests
import re
import urllib.parse
from datetime import datetime

# ==========================================
# 1. CONFIG & SETUP
# ==========================================
st.set_page_config(page_title="R4R Stealth Scanner", layout="wide")

st.sidebar.title("⚙️ Scanner Settings")

# --- SECTION A: DEMOGRAPHICS ---
st.sidebar.header("1. Target")
target_genders = st.sidebar.multiselect("Gender Tags", ['F4M', 'F4R', 'F4F', 'M4F'], default=['F4M'])
min_age, max_age = st.sidebar.slider("Age Range", 18, 99, (21, 35))

# --- SECTION B: CONTENT FILTERS ---
st.sidebar.header("2. Filtering Rules")

enable_exclude = st.sidebar.checkbox("⛔ Enable Block List", value=True)
exclude_text = st.sidebar.text_area("Block words (comma separated)", "smoke, 420, poly, married, couple, trans", height=60)
exclude_keywords = [k.strip().lower() for k in exclude_text.split(",") if k.strip()]

enable_include = st.sidebar.checkbox("✅ Enable 'Must Have'", value=False)
include_text = st.sidebar.text_area("Must contain (comma separated)", "local, nyc, gamer, nurse, gym", height=60)
include_keywords = [k.strip().lower() for k in include_text.split(",") if k.strip()]

# Quick Blockers
st.sidebar.subheader("⚡ Quick Blocks")
block_sellers = st.sidebar.checkbox("Block Sellers (OF/Fansly)", value=True)
block_crypto  = st.sidebar.checkbox("Block Crypto/Spam", value=True)

SELLER_TERMS = ["onlyfans", "fansly", "selling", "promo", "prices", "cashapp", "paypal", "menu"]
CRYPTO_TERMS = ["crypto", "bitcoin", "telegram", "whatsapp", "invest"]

# --- SECTION C: YOUR PERSONA ---
st.sidebar.header("3. Reply Assistant")
my_interests = st.sidebar.text_area("Your Hobbies (for drafts)", "tennis and video games")
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
    author = post['author']
    full_text = post['full_text']
    
    # Keyword detection for replies
    if any(k in full_text for k in ['tennis', 'sport', 'gym', 'active']):
        draft = f"Hey! Saw your post and noticed the active/tennis mention. I'm big into tennis myself. Liked your vibe in the post. Up for a chat? -{my_name}"
    elif any(k in full_text for k in ['game', 'gaming', 'steam', 'pc', 'play']):
        draft = f"Hey! Saw you're into gaming. I play a lot on PC/Console (mainly {my_interests}). Liked your intro. Up for a game or chat? -{my_name}"
    else:
        draft = f"Hi! Read your post about '{post['title'][:30]}...' and thought you sounded cool. I'm mainly into {my_interests} but down to chat about whatever. -{my_name}"
    
    # Reddit Chat URL
    return f"https://www.reddit.com/chat/u/{author}", draft

def parse_post(child):
    data = child['data']
    title = data.get('title', '')
    selftext = data.get('selftext', '')
    
    pattern = r"(\d{2})\s*[\[\(]([Ff]4[MmRrFf])[\]\)]"
    match = re.search(pattern, title)
    age = int(match.group(1)) if match else None
    tag = match.group(2).upper() if match else None
    
    return {
        "title": title,
        "full_text": (title + " " + selftext).lower(),
        "url": data.get('url'),
        "created_utc": data.get('created_utc'),
        "author": data.get('author'),
        "age": age,
        "tag": tag,
        "preview": selftext[:500]
    }

def passes_filters(post):
    if not post['age']: return False
    if not (min_age <= post['age'] <= max_age): return False
    
    # Check Gender (Redundant with search query but good safety)
    if target_genders and post['tag'] not in target_genders: return False

    text = post['full_text']
    if enable_exclude and contains_word(text, exclude_keywords): return False
    if enable_include and not contains_word(text, include_keywords): return False
    if block_sellers and contains_word(text, SELLER_TERMS): return False
    if block_crypto and contains_word(text, CRYPTO_TERMS): return False
    return True

def fetch_reddit_data():
    # 1. Build Query: subreddit:r4r AND (title:"F4M" OR title:"F4R")
    if target_genders:
        tags_query = " OR ".join([f'title:"{t}"' for t in target_genders])
        q = f'subreddit:r4r ({tags_query})'
    else:
        q = 'subreddit:r4r'
        
    params = {
        'q': q,
        'sort': 'new',
        'restrict_sr': 'on',
        'limit': '50'
    }
    
    # 2. Fake Browser Headers (Crucial)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }
    
    url = "https://www.reddit.com/r/r4r/search.json"
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()['data']['children']
        elif r.status_code == 429:
            st.error("❌ Too Many Requests. Reddit is rate-limiting this server.")
        elif r.status_code == 403:
            st.error("❌ Forbidden. Reddit blocked this IP.")
        else:
            st.error(f"❌ Error {r.status_code}")
            
    except Exception as e:
        st.error(f"Connection Failed: {e}")
        
    return []

# ==========================================
# 3. MAIN UI
# ==========================================
st.title("🕵️ R4R Stealth Scanner")

tab1, tab2 = st.tabs(["🚀 Live Scanner", "ℹ️ Help"])

with tab1:
    if st.button("Scan Now"):
        with st.spinner("Connecting to Reddit..."):
            posts = fetch_reddit_data()
            
            if posts:
                count = 0
                for child in posts:
                    post = parse_post(child)
                    if passes_filters(post):
                        count += 1
                        chat_link, draft = generate_reply_data(post)
                        
                        with st.expander(f"[{post['tag']}] {post['age']} | {post['title']}"):
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.write(post['preview'] + "...")
                                st.markdown(f"[🔗 View Post]({post['url']})")
                            with col2:
                                st.text_area("Draft", draft, height=100, key=post['url'])
                                st.markdown(f"""<a href="{chat_link}" target="_blank"><button style="background-color:#FF4500;color:white;border:none;padding:10px;border-radius:4px;width:100%;">💬 Chat</button></a>""", unsafe_allow_html=True)
                
                if count > 0:
                    st.success(f"Found {count} matches!")
                else:
                    st.warning("Data received, but your filters hid everything. Try unchecking 'Must Have'.")
            else:
                # If posts is empty, the error was likely printed in the try/except block above
                pass

with tab2:
    st.write("If you get a 429/403 error, run this script locally on your PC using 'streamlit run app.py'")
