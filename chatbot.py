import streamlit as st
from groq import Groq
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd

# تنظیمات اولیه صفحه
st.set_page_config(page_title="Audit Research Assistant", layout="centered")
st.title("🤖 دستیار هوشمند پژوهش حسابرسی")

# ۱. اتصال به دیتابیس ابری (Supabase)
# آدرس دیتابیس را قبلاً در بخش Secrets با نام DB_URL ذخیره کرده‌اید
try:
    engine = create_engine(st.secrets["DB_URL"])
except Exception as e:
    st.error("خطا در پیکربندی دیتابیس. لطفاً تنظیمات Secrets را بررسی کنید.")

# ۲. تابع ذخیره‌سازی داده‌ها (Data Logging)
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
        # خطا در کنسول چاپ می‌شود تا کاربر متوجه نشود و تجربه کاربری خراب نشود
        print(f"Database Save Error: {e}")

# ۳. تنظیمات Groq API
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# مدیریت حافظه گفتگو (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []

# نمایش پیام‌های قبلی
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ۴. فرآیند دریافت پیام و پاسخ‌دهی
if prompt := st.chat_input("سوال خود را در زمینه حسابرسی بپرسید..."):
    # افزودن پیام کاربر به تاریخچه و نمایش آن
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # آماده‌سازی پیام‌ها برای مدل (حذف پیام‌های احتمالی None)
    current_chat_history = [
        {"role": m["role"], "content": m["content"]} 
        for m in st.session_state.messages 
        if m["content"]
    ]

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # فراخوانی مدل Groq
            completion = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=current_chat_history,
                stream=True,
            )
            
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)

            # ۵. ذخیره‌سازی خودکار در دیتابیس (پس از دریافت پاسخ کامل)
            # محاسبه شماره ردیف پیام در گفتگو
            current_index = (len(st.session_state.messages) // 2) + 1
            save_interaction(
                u_id="Anonymous_User", 
                p_num=current_index,
                u_prompt=prompt,
                ai_res=full_response
            )
            
            # ذخیره پاسخ در حافظه برای ادامه گفتگو
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"متأسفانه خطایی در مدل رخ داد: {str(e)}")

