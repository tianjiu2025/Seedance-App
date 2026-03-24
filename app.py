import streamlit as st
import time
import requests
import base64
from supabase import create_client, Client
import extra_streamlit_components as stx

# ================= 1. 核心配置与 API 密钥 =================
st.set_page_config(page_title="魔方国际影业 - AI 创作站", page_icon="🎬", layout="wide")

def log_api_error(msg):
    st.error(msg)

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    SEEDANCE_API_TOKEN = st.secrets["SEEDANCE_API_TOKEN"]
    CREATE_URL = st.secrets.get("CREATE_URL", "http://118.196.64.1/api/v1/doubao/create") 
    GET_URL = st.secrets.get("GET_URL", "http://118.196.64.1/api/v1/doubao/get_result") 
except Exception as e:
    st.error(f"❌ 必填 Secrets 配置缺失: {e}")
    st.stop()

# ================= 2. 记忆芯片与登录逻辑 =================
cookie_manager = stx.CookieManager(key="mofang_mgr")
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

stored_user = cookie_manager.get(cookie="mgr_user")
stored_role = cookie_manager.get(cookie="mgr_role")

if stored_user and stored_role and not st.session_state["logged_in"]:
    st.session_state["logged_in"] = True
    st.session_state["username"] = stored_user
    st.session_state["role"] = stored_role

if not st.session_state["logged_in"]:
    st.markdown("<br><br><h2 style='text-align: center;'>🔐 魔方国际影业 - 内部系统</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.info("💡 请使用管理员分配的专属账号登录。")
        user_input = st.text_input("👤 员工账号")
        pwd_input = st.text_input("🔑 登录密码", type="password")
        
        if st.button("🚀 登录系统", use_container_width=True):
            users = {
                "admin": {"pwd": "888888", "name": "天九老板", "role": "admin"},
                "yuangong1": {"pwd": "123456", "name": "剪辑师小王", "role": "employee"},
                "zhangsan": {"pwd": "666888", "name": "特效师张三", "role": "employee"},
                "lisi": {"pwd": "222222", "name": "原画师李四", "role": "employee"},
                "wangwu": {"pwd": "333333", "name": "音效师王五", "role": "employee"},
                "zhaoliu": {"pwd": "444444", "name": "模型师赵六", "role": "employee"},
                "sunqi": {"pwd": "555555", "name": "动画师孙七", "role": "employee"},
                "zhouba": {"pwd": "666666", "name": "编剧周八", "role": "employee"},
                "wujiu": {"pwd": "777777", "name": "运营吴九", "role": "employee"}
            }
            
            if user_input in users and users[user_input]["pwd"] == pwd_input:
                user_info = users[user_input]
                st.session_state["logged_in"] = True
                st.session_state["username"] = user_info["name"]
