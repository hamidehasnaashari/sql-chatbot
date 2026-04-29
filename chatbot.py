import streamlit as st
from groq import Groq
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd

# تنظیمات اصلی صفحه
st.set_page_config(page_title="SQL Server Expert Consultant", layout="centered")
st.title("🛡️ مشاور تخصصی SQL Server")
st.subheader("پایگاه دانش طراحی، بهینه‌سازی و امنیت دیتابیس")

# ۱. اتصال امن به دیتابیس Supabase
try:
    engine = create_engine(st.secrets["DB_URL"])
except Exception as e:
    st.error("خطا در پیکربندی دیتابیس. لطفاً Secrets را بررسی کنید.")

# ۲. تابع ذخیره‌سازی برای تحلیل‌های آتی (Forensic & Audit)
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
        print(f"Database Save Error: {e}")

# ۳. تنظیمات Groq با مدل جدید Llama 3.3
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# تعریف هویت تخصصی چت‌بات در حافظه گفتگو
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": "You are a world-class SQL Server Consultant. Your expertise includes T-SQL, Database Design (Normalization), Indexing, Performance Tuning, and SQL Server Audit. Provide professional and technical advice."
        }
    ]

# نمایش تاریخچه چت (به جز پیام سیستم)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ۴. منطق دریافت پرسش و تولید پاسخ
if prompt := st.chat_input("سوال فنی خود درباره SQL Server را بپرسید..."):
    # ثبت پیام کاربر
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # فیلتر پیام‌ها برای ارسال به مدل
    safe_history = [m for m in st.session_state.messages if m["content"]]

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # استفاده از مدل جدید و پشتیبانی شده
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=safe_history,
                stream=True,
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)

            # ۵. ذخیره‌سازی خودکار در Supabase برای تحقیق شما
            current_index = (len(st.session_state.messages) // 2)
            save_interaction(
                u_id="SQL_Researcher", 
                p_num=current_index,
                u_prompt=prompt,
                ai_res=full_response
            )
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"خطای مدل: {str(e)}")

