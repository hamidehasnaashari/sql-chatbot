import streamlit as st
from groq import Groq
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
# تنظیمات اصلی صفحه
st.set_page_config(page_title="SQL Server AI Consultant", layout="wide")

# 2. Professional UI Styling (Clean & Bordered)
st.markdown("""
    <style>
    .main { padding: 2rem; }
    .stApp {
        background-color: #f8f9fa;
        color: #212529;
    }
    .main-container {
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 25px;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .bot-info {
        background-color: #e9ecef;
        border-left: 5px solid #0d6efd;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Header & Introduction
with st.container():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2721/2721614.png", width=80)
    with col2:
        st.title("AI-Powered SQL Server Consultant")
        st.subheader("Intelligent Database Optimization & Analysis System")

# Professional Description for the Professor
st.markdown("""
    <div class="bot-info">
        <b>Project Overview:</b><br>
        This AI agent is powered by LLM and Cloud database (PostgreSQL)</b> backend 
        to log auditing trails. It is designed to assist with:<br>
        <ul>
            <li>T-SQL Query Optimization & Debugging</li>
            <li>Database Schema Design & Data Modeling</li>
            <li>Performance Tuning & Indexing Strategies</li>
                   </ul>
    </div>
    """, unsafe_allow_html=True)


# ۱. اتصال به دیتابیس Supabase
try:
    engine = create_engine(st.secrets["DB_URL"])
except Exception as e:
    st.error("خطا در تنظیمات دیتابیس.")

# ۲. تابع اصلاح شده برای ذخیره‌سازی داده‌ها
def save_interaction(u_id, p_num, u_prompt, ai_res):
    insert_query = text("""
        INSERT INTO audit_logs (user_id, prompt_number, user_prompt, ai_response, timestamp)
        VALUES (:u_id, :p_num, :u_prompt, :ai_res, :ts)
    """)
    try:
        with engine.begin() as conn:
            conn.execute(insert_query, {
                "u_id": u_id,
                "p_num": p_num,
                "u_prompt": u_prompt,
                "ai_res": ai_res,
                "ts": datetime.now()
            })
    except Exception as e:
        print(f"Database Error: {e}")

# ۳. تنظیمات Groq
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a professional SQL Server Consultant. Provide technical advice on T-SQL, Indexing, and Database Design."}
    ]

# نمایش پیام‌ها
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# Create a layout for the input and the exit button
col_input, col_exit = st.columns([6, 1])

with col_exit:
    # This button resets the entire session and returns to the home view
    if st.button("🚪 Exit & Home", use_container_width=True, help="End session and return to home page"):
        # Clear chat history and any other session-specific data
        st.session_state.messages = [{"role": "system", "content": "You are a professional SQL Server Expert."}]
        # If you have other state variables like login status, clear them here
        st.rerun()
        
# ۴. بخش اصلی گفتگو و ذخیره‌سازی (اصلاح شده برای رفع NameError)
with col_input:
if prompt := st.chat_input("َAsk your question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = "" # تعریف متغیر در ابتدای بلاک
        
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                stream=True,
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # ذخیره‌سازی دقیقاً در همین بلاک که متغیر تعریف شده است
            current_index = (len(st.session_state.messages) // 2) + 1
            save_interaction(
                u_id="SQL_Researcher", 
                p_num=current_index,
                u_prompt=prompt,
                ai_res=full_response
            )
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"خطا در مدل: {str(e)}")


# تست سریع اتصال در سایدبار
#if st.sidebar.button("تست نهایی اتصال"):
 #   import urllib.parse
  #  try:
        # نمایش اطلاعات پایه برای دیباگ (بدون نمایش پسورد)
   #     db_url = st.secrets["DB_URL"]
    #    st.sidebar.info(f"Connecting to: {db_url.split('@')[-1]}")
        
     #   with engine.connect() as conn:
      #      conn.execute(text("SELECT 1"))
       #     st.sidebar.success("تبریک! اتصال برقرار شد و آماده ذخیره‌سازی است. ✅")
    #except Exception as e:
     #   st.sidebar.error("خطای سیستمی:")
      #  st.sidebar.code(str(e)) # نمایش کد خطا برای بررسی دقیق‌تر
