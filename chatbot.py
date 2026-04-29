import streamlit as st
from groq import Groq
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd

# تنظیمات اولیه صفحه
st.set_page_config(page_title="Audit Research Chatbot", layout="centered")
st.title("🤖 دستیار پژوهش حسابرسی")
st.write("این گفتگو برای اهداف تحقیقاتی در دیتابیس امن ذخیره می‌شود.")

# ۱. اتصال به دیتابیس ابری (با استفاده از رازی که در Secrets گذاشتید)
try:
    engine = create_engine(st.secrets["DB_URL"])
except Exception as e:
    st.error("خطا در اتصال به دیتابیس. لطفاً Secrets را چک کنید.")

# ۲. تابع ذخیره‌سازی داده‌ها (Invisible Data Collection)
def save_data(u_id, p_num, u_prompt, ai_res):
    query = text("""
        INSERT INTO audit_logs (user_id, prompt_number, user_prompt, ai_response, timestamp)
        VALUES (:u_id, :p_num, :u_prompt, :ai_res, :ts)
    """)
    try:
        with engine.begin() as conn:
            conn.execute(query, {
                "u_id": u_id,
                "p_num": p_num,
                "u_prompt": u_prompt,
                "ai_res": ai_res,
                "ts": datetime.now()
            })
    except Exception as e:
        print(f"Database Error: {e}")

# ۳. تنظیمات مدل هوش مصنوعی (Groq)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

# نمایش تاریخچه چت در محیط برنامه
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ۴. منطق اصلی چت و ذخیره‌سازی
if prompt := st.chat_input("سوال خود را اینجا بپرسید..."):
    # نمایش پیام کاربر
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # گرفتن پاسخ از Groq
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
            stream=True,
        )
        
        for chunk in completion:
            full_response += (chunk.choices[0].delta.content or "")
            response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)

    # ۵. عملیات ذخیره‌سازی (بدون اینکه کاربر متوجه شود)
    # به عنوان یک Audit Manager، ما هر تعامل را با شماره ردیف ثبت می‌کنیم
    prompt_index = len(st.session_state.messages) // 2 + 1
    save_data(
        u_id="Anonymous_Researcher", # می‌توانید این را بر اساس کد شرکت‌کننده تغییر دهید
        p_num=prompt_index,
        u_prompt=prompt,
        ai_res=full_response
    )
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# ۶. بخش مدیریت (فقط برای شما با رمز عبور) - اختیاری
with st.sidebar:
    st.header("پنل مدیریت")
    admin_pass = st.text_input("رمز عبور مدیر", type="password")
    if admin_pass == st.secrets.get("ADMIN_PASSWORD", "1234"): # رمزی در Secrets تعریف کنید
        st.success("دسترسی تایید شد")
        if st.button("مشاهده وضعیت لحظه‌ای دیتابیس"):
            df = pd.read_sql("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 5", engine)
            st.table(df)
