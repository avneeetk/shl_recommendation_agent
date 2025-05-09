import streamlit as st
import sys
from pathlib import Path
import requests  

sys.path.append(str(Path(__file__).parent.parent))


st.set_page_config(page_title="SHL Recommendation Assistant", page_icon="📚")

st.title("🤖 SHL Assessment Recommender")
st.markdown("Ask a question like _'I want to evaluate programming skills'_ or _'Give me tests for verbal ability'_.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.chat_input("What are you looking for today?")
if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
   
    response = requests.post("https://shl-recommendation-agent-1.onrender.com/api/v1/recommend", json={"query": user_input})

    results = response.json().get("results", []) if response.status_code == 200 else []

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

for chat in st.session_state.chat_history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"], unsafe_allow_html=True)