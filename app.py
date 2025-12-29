import streamlit as st
import feedparser
import re
from datetime import datetime

# ==========================================
# 1. SETUP
# ==========================================
st.set_page_config(page_title="R4R Assistant (Chat Version)", layout="wide")

# ==========================================
# 2. CONFIGURATION
# ==========================================
st.sidebar.header("1. Target Demographics")
target_genders = st.sidebar.multiselect("Target Tags", ['F4M', 'F4R', 'F4F'], default=['F4M'])
min_age, max_age = st.sidebar.slider("Age Range", 18, 99, (21, 35))

st.sidebar.divider()
st.sidebar.header("2. Your Persona")
my_interests = st.sidebar.text_area("Your Hobbies", "tennis and video games")
my_name = st.sidebar.text_input("Your Name/Sign-off", "Me")

# ==========================================
# 3. SMART REPLY LOGIC
# ==========================================
def generate_reply_data(post):
    """Generates the draft text and the Chat URL."""
    
    # Clean up author name for the URL
    # RSS usually gives "/u/username", we need just "username"
    author_raw = post.get('author', 'unknown')
    author_clean = author_raw.replace('/u/', '').replace('u/', '').strip()
    
    # 1. Analyze Context
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

    # 2. Create the Chat Link
    # This opens the Reddit Chat UI directly for that user
    chat_link = f"https://www.reddit.com/chat/u/{author_clean}"
    
    return chat_link, draft, author_clean

# ==========================================
# 4. PARSING & FILTERING
# ==========================================
def parse_entry(entry):
    title = entry.title
    # Safely get content
    content = entry.content[0].value if 'content' in entry else ""
    
    # Safely get author (RSS feeds sometimes act weird with authors)
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
    if not post['age'] or not post['tag']: return False
    if post['tag'] not in target_genders: return False
    if not (min_age <= post['age'] <= max_age): return False
    
    # Simple Block List
    block_words = ["onlyfans", "fansly", "selling", "promo", "cashapp", "paypal"]
    
    # Word boundary check to prevent "sub" matching "subject"
    text = f" {post['full_text']} "
    for word in block_words:
        if f" {word} " in text:
            return False
            
    return True

def fetch_rss():
    url = "https://www.reddit.com/r/r4r/new.rss"
    return feedparser.parse(url, agent="Mozilla/5.0").entries

# ==========================================
# 5. MAIN UI
# ==========================================
st.title("🎾 R4R Assistant (Chat Mode)")

tab1, tab2 = st.tabs(["🔍 Live Feed", "⚙️ Help"])

with tab1:
    if st.button("Check Feed"):
        entries = fetch_rss()
        count = 0
        for entry in entries:
            post = parse_entry(entry)
            if passes_filters(post):
                count += 1
                
                chat_link, draft_text, username = generate_reply_data(post)
                
                with st.expander(f"[{post['tag']}] {post['age']} | {post['title']}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**User:** {username} | **Posted:** {post['published']}")
                        st.info(post['content'][:400] + "...")
                        st.markdown(f"[🔗 View Original Post]({post['link']})")
                    
                    with col2:
                        st.write("### 👇 Step 1: Copy")
                        st.text_area("Draft (Ctrl+C)", draft_text, height=120, key=post['link'])
                        
                        st.write("### 👇 Step 2: Chat")
                        st.markdown(
                            f"""
                            <a href="{chat_link}" target="_blank">
                                <button style="
                                    background-color:#0079D3; 
                                    color:white; 
                                    padding:12px; 
                                    border:none; 
                                    border-radius:20px; 
                                    font-weight: bold;
                                    cursor:pointer; 
                                    width:100%;">
                                    💬 Open Chat with {username}
                                </button>
                            </a>
                            """, 
                            unsafe_allow_html=True
                        )
        if count == 0:
            st.warning("No matches found.")

with tab2:
    st.write("Reddit Chat does not allow auto-filling text. You must copy the draft manually.")
