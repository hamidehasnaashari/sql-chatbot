import streamlit as st
from groq import Groq
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
# تنظیمات اصلی صفحه
st.set_page_config(page_title="SQL Server Expert", layout="wide")

# CSS برای ایجاد حاشیه، فونت فارسی و استایل کادرها
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .main-container {
        border: 2px solid #e6e9ef;
        border-radius: 15px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .bot-description {
        background-color: #f0f2f6;
        border-right: 5px solid #007bff;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
        direction: rtl;
    }
    .stChatMessage {
        border: 1px solid #ddd;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# هدر و معرفی بات
with st.container():
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/2721/2721614.png", width=100) # آیکون دیتابیس
    with col2:
        st.title("دستیار هوشمند مدیریت دیتابیس")
        st.markdown("### متخصص بهینه‌سازی SQL Server و تحلیل داده")

# بخش توضیحات بات (خلاصه توانمندی‌ها)
st.markdown("""
    <div class="bot-description">
        <b>درباره این دستیار:</b><br>
        این هوش مصنوعی بر پایه مدل Llama 3.3 طراحی شده و در زمینه‌های زیر به شما کمک می‌کند:<br>
        <ul>
            <li>عیب‌یابی کوئری‌های پیچیده T-SQL</li>
            <li>طراحی و نرمال‌سازی مدل‌های داده (Data Modeling)</li>
            <li>بهینه‌سازی ایندکس‌ها و افزایش سرعت دیتابیس</li>
            <li>مشاوره در زمینه Forensic Accounting و شناسایی الگوهای مشکوک در تراکنش‌ها</li>
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
