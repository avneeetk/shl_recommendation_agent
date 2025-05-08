import streamlit as st
import sys
from pathlib import Path
import requests  # Added for API communication

sys.path.append(str(Path(__file__).parent.parent))

# For direct function call (choose one):
# from src.core.recommender import search_pinecone

st.set_page_config(page_title="SHL Recommendation Assistant", page_icon="📚")

st.title("🤖 SHL Assessment Recommender")
st.markdown("Ask a question like _'I want to evaluate programming skills'_ or _'Give me tests for verbal ability'_.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User Input
user_input = st.chat_input("What are you looking for today?")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Choose either direct function call or API request:
    
    # Option 1: Direct function call
    # results = search_pinecone(user_input)
    
    # Option 2: API request (requires running FastAPI server)
    response = requests.post(
        "http://localhost:8000/recommend",
        json={"query": user_input}
    )
    results = response.json().get("results", []) if response.status_code == 200 else []

    # Format response with detailed cards
    if results:
        response_content = "## Recommended Assessments\n\n"
        for r in results:
            response_content += f"""
### {r['name']}
**Type**: {r['type']}  
**Remote**: {r.get('remote', 'N/A')}  
**IRT Support**: {r.get('irt', 'N/A')}  
[🔗 View Test]({r['url']})  
**Confidence Score**: {r['score']:.3f}

---
"""
    else:
        response_content = "⚠️ No matching assessments found. Please try a different query."

    st.session_state.chat_history.append({"role": "assistant", "content": response_content})

# Display chat history
for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"], unsafe_allow_html=True)