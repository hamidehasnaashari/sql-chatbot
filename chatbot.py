import streamlit as st
from groq import Groq
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd

# تنظیمات اصلی صفحه
# تنظیمات اصلی صفحه با تم تیره/روشن بهبود یافته
st.set_page_config(page_title="SQL Server Expert Consultant", layout="wide", initial_sidebar_state="expanded")

# اضافه کردن CSS سفارشی برای ظاهر مرتب‌تر
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .sidebar .sidebar-content {
        background-image: linear-gradient(#2e7bcf,#2e7bcf);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# هدر اصلی
col1, col2 = st.columns([1, 5])
with col1:
    st.title("🛡️")
with col2:
    st.title("مشاور ارشد SQL Server")
    st.caption("سیستم هوشمند تحلیل و بهینه‌سازی پایگاه داده")

st.divider()


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

# ۴. بخش اصلی گفتگو و ذخیره‌سازی (اصلاح شده برای رفع NameError)
if prompt := st.chat_input("سوال فنی خود را بپرسید..."):
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
