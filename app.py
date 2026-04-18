import streamlit as st
import requests
import json
import time
import pandas as pd
from bs4 import BeautifulSoup

# --- Configuration & Styling ---
st.set_page_config(page_title="SEO Content Gap Analyser", layout="wide")
st.title("🔍 SEO Content Gap Analyser")
st.markdown("Compare a live webpage against AlsoAsked intent data to find missing content opportunities.")

# --- Sidebar (Secure Settings) ---
with st.sidebar:
    st.header("⚙️ Settings")
    # Securely take the API key (masks input with asterisks)
    api_key = st.text_input("AlsoAsked API Key", type="password", help="Your key is not stored permanently.")
    region = st.selectbox("Search Region", ["gb", "us", "au", "ca"], index=0)
    fresh_data = st.checkbox("Force Fresh Search", value=False, help="Check to scrape Google live. Uncheck to use cached data (saves credits).")
    
    st.markdown("---")
    st.markdown("**Local LLM Status**")
    st.info("Using Ollama model: `gemma4:e4b` at `http://127.0.0.1:11434`")
    st.markdown("---")
    st.markdown("Created by [Atkinson Smith Digital](https://atkinsonsmithdigital.com)")

# --- Core Functions (Translated from Node.js) ---

def get_also_asked_questions(api_key, term, region, fresh):
    url = 'https://alsoaskedapi.com/v1/search'
    headers = {
        'Content-Type': 'application/json',
        'X-Api-Key': api_key
    }
    payload = {
        "terms": [term.strip()],
        "language": "en",
        "region": region,
        "depth": 2,
        "fresh": fresh,
        "notify_webhooks": False
    }

    res = requests.post(url, headers=headers, json=payload)
    if not res.ok:
        st.error(f"AlsoAsked API Error ({res.status_code}): {res.text}")
        st.stop()

    data = res.json()

    # Polling loop if the API is scraping live
    while data.get('status') in ['queued', 'processing', 'running', 'pending']:
        st.toast(f"AlsoAsked is scraping Google live (Status: {data.get('status')}). Waiting 5s...")
        time.sleep(5)
        
        search_id = data.get('id') or data.get('search_id')
        if search_id:
            res = requests.get(f"https://alsoaskedapi.com/v1/search/{search_id}", headers=headers)
            data = res.json()
        else:
            st.error("API is running but provided no Job ID to track.")
            st.stop()

    if data.get('status') != 'success' or not data.get('queries'):
        return []

    # Recursive function to flatten the nested questions array
    def flatten_results(questions):
        flattened = []
        for q in questions:
            flattened.append(q['question'])
            if q.get('results'):
                flattened.extend(flatten_results(q['results']))
        return flattened

    results_array = data['queries'][0].get('results', [])
    return list(set(flatten_results(results_array)))

def fetch_page_text(url):
    try:
        # 1. Define fake browser headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # 2. Pass the headers into the get request
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
            
        # Extract and clean text
        text = ' '.join(soup.stripped_strings)
        return text[:6000] # Limit to avoid context window overload
    except Exception as e:
        st.error(f"Failed to fetch webpage text: {str(e)}")
        st.stop()

def analyze_with_gemma(questions, page_text):
    url = "http://127.0.0.1:11434/v1/chat/completions"
    payload = {
        "model": "gemma4:e4b",
        "response_format": { "type": "json_object" },
        "messages": [
            {
                "role": "system",
                "content": "You are a strict SEO data evaluator. I will provide page text and a JSON array of questions. Evaluate each question against the text. Return ONLY a JSON object with a single key 'evaluations' containing an array of objects. Each object must have 'question' (string) and 'is_answered' (boolean)."
            },
            {
                "role": "user",
                "content": f"Questions: {json.dumps(questions)}\n\nPage Text: {page_text}"
            }
        ],
        "temperature": 0.0 # Dropping to 0.0 makes it even more strictly logical
    }

    try:
        res = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        if not res.ok:
            st.error(f"Local LLM Error ({res.status_code}): {res.text}")
            st.stop()
            
        data = res.json()
        content = data['choices'][0]['message']['content']
        result_json = json.loads(content)
        
        # Sort the LLM's new format back into our two clean lists for the UI
        answered = []
        unanswered = []
        
        for item in result_json.get('evaluations', []):
            if item.get('is_answered') is True:
                answered.append(item.get('question'))
            else:
                unanswered.append(item.get('question'))
                
        return {
            "answered_questions": answered,
            "unanswered_questions": unanswered
        }
        
    except Exception as e:
        st.error(f"Failed to parse Gemma response: {str(e)}")
        st.stop()

# --- User Interface ---

col1, col2 = st.columns(2)
with col1:
    target_url = st.text_input("Enter Page URL", placeholder="https://example.com/topic")
with col2:
    target_keyword = st.text_input("Enter Target Keyword / Topic", placeholder="e.g. Content Marketing")

if st.button("🚀 Analyse Content Gap", use_container_width=True, type="primary"):
    if not api_key:
        st.warning("Please enter your AlsoAsked API key in the sidebar first.")
        st.stop()
    if not target_url or not target_keyword:
        st.warning("Please provide both a URL and a Target Keyword.")
        st.stop()

    with st.status("Analyzing...", expanded=True) as status:
        st.write("📥 Fetching questions from AlsoAsked...")
        questions = get_also_asked_questions(api_key, target_keyword, region, fresh_data)
        
        if not questions:
            status.update(label="No questions found for this topic.", state="error")
            st.stop()
            
        st.write(f"✅ Found {len(questions)} intent questions.")
        
        st.write("🌐 Scraping target webpage text...")
        page_text = fetch_page_text(target_url)
        
        st.write("🧠 Analyzing content overlap with local Gemma...")
        analysis = analyze_with_gemma(questions, page_text)
        
        status.update(label="Analysis Complete!", state="complete", expanded=False)

    # Display Results side-by-side
    answered = analysis.get("answered_questions", [])
    unanswered = analysis.get("unanswered_questions", [])

    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.success(f"✅ Answered Questions ({len(answered)})")
        for q in answered:
            st.write(f"- {q}")
            
    with res_col2:
        st.error(f"❌ Unanswered Questions ({len(unanswered)})")
        for q in unanswered:
            st.write(f"- {q}")

    # Prepare Data for CSV Export
    st.markdown("---")
    
    # We pad the lists with empty strings so they are the same length for the CSV DataFrame
    max_len = max(len(answered), len(unanswered))
    padded_answered = answered + [""] * (max_len - len(answered))
    padded_unanswered = unanswered + [""] * (max_len - len(unanswered))
    
    df = pd.DataFrame({
        "Answered Questions": padded_answered,
        "Unanswered Questions": padded_unanswered
    })
    
    csv = df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name=f"content_gap_{target_keyword.replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=True
    )