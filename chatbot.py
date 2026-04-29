import streamlit as st
from groq import Groq
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd

# تنظیمات اصلی صفحه
st.set_page_config(page_title="SQL Server Expert", layout="centered")
st.title("🛡️ مشاور تخصصی SQL Server")

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


                st.table(df)
            except Exception as e:
                st.error("خطا در بارگذاری جدول.")
