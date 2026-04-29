#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
from groq import Groq
import sqlite3
from datetime import datetime

# ۱. تنظیمات اولیه دیتابیس
def init_db():
    conn = sqlite3.connect('audit_study_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chat_logs 
                 (user_id TEXT, 
                  prompt_number INTEGER, 
                  user_prompt TEXT, 
                  ai_response TEXT, 
                  model_name TEXT,
                  timestamp TEXT)''')
    conn.commit()
    return conn

# ۲. اتصال امن به Groq
# حتماً در پنل Streamlit Cloud، کلید را در بخش Secrets با نام GROQ_API_KEY وارد کنید
try:
    client = Groq(api_key=st.secrets["API_KEY"])
except Exception as e:
    st.error("خطا: کلید API در بخش Secrets تنظیم نشده است.")
    st.stop()

st.set_page_config(page_title="SQL Consultant AI", layout="centered")

st.title("دستیار هوشمند و مشاور کدهای SQL")
st.info("این پنل جهت مشاوره در طراحی دیتابیس و بهینه‌سازی کوئری‌ها طراحی شده است.")

# ۳. مدیریت شناسایی کاربر
if 'user_id' not in st.session_state:
    st.session_state.user_id = ""
if 'p_count' not in st.session_state:
    st.session_state.p_count = 0
if "messages" not in st.session_state:
    st.session_state.messages = []

user_input_id = st.text_input("لطفاً کد شناسایی خود را وارد کنید:", value=st.session_state.user_id)

if user_input_id:
    st.session_state.user_id = user_input_id

    # نمایش تاریخچه چت
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ۴. فرآیند دریافت پرامپت و پاسخ
    if prompt := st.chat_input("سوال SQL خود را اینجا بپرسید (مثلاً: چطور دو جدول را Join کنم؟)"):
        st.session_state.p_count += 1
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # فراخوانی مدل به عنوان مشاور SQL
        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant", 
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert SQL Consultant. Help the user write, optimize, and debug SQL queries. Focus on best practices, T-SQL (SQL Server) syntax, data modeling, and performance. Always wrap SQL code in backticks for better formatting."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5, # کاهش دما برای پاسخ‌های دقیق‌تر فنی
            )
            response_text = completion.choices[0].message.content
        except Exception as e:
            response_text = f"خطای سیستمی: {str(e)}"

        # نمایش پاسخ
        with st.chat_message("assistant"):
            st.markdown(response_text)
        st.session_state.messages.append({"role": "assistant", "content": response_text})

        # ۵. ذخیره در دیتابیس
        conn = init_db()
        c = conn.cursor()
        c.execute("INSERT INTO chat_logs VALUES (?, ?, ?, ?, ?, ?)", 
                  (st.session_state.user_id, 
                   st.session_state.p_count, 
                   prompt, 
                   response_text, 
                   "Llama-3.1-8b-SQL", 
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

else:
    st.warning("برای شروع مشاوره، لطفاً کد شناسایی را وارد کنید.")

# دکمه اتمام جلسه در انتهای صفحه
st.divider()
if st.button("اتمام جلسه و خروج"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("اطلاعات جلسه پاکسازی شد. از همراهی شما متشکریم.")
    st.balloons()
    st.rerun()

