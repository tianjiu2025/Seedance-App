import streamlit as st
import time
import requests
import uuid
from supabase import create_client, Client

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

# ================= 2. 极简稳定版登录逻辑 =================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

# 初始化视频历史画廊缓存池
if "video_history" not in st.session_state:
    st.session_state["video_history"] = []

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
                "zhangsan": {"pwd": "666888", "name": "特效师张三", "role": "employee"}
            }
            if user_input in users and users[user_input]["pwd"] == pwd_input:
                user_info = users[user_input]
                st.session_state["logged_in"] = True
                st.session_state["username"] = user_info["name"]
                st.session_state["role"] = user_info["role"]
                st.rerun() 
            else:
                st.error("⚠️ 账号或密码错误！")
    st.stop()

# ================= 3. 侧边栏 =================
st.sidebar.title(f"👤 {st.session_state['username']}")
st.sidebar.caption(f"当前身份: {'👑 超级管理员' if st.session_state['role'] == 'admin' else '💼 内部员工'}")
if st.sidebar.button("退出登录"):
    st.session_state["logged_in"] = False
    st.session_state["video_history"] = [] # 退出时清空个人画廊
    st.rerun()

if st.session_state["role"] == "admin":
    st.title("📊 财务与算力控制台")
    try:
        response = supabase.table("token_logs").select("*").order("created_at", desc=True).execute()
        if response.data: st.dataframe(response.data, use_container_width=True)
        else: st.info("暂无生成记录。")
    except Exception as e: st.error(f"数据库连接失败: {e}")

# ================= 4. 员工真实创作台 =================
else:
    st.markdown("## 🎬 魔方国际影业 - Seedance 2.0 视频生成台")

    # 顶部分区：控制面板
    with st.container(border=True):
        prompt = st.text_area(
            "📝 画面描述 (Prompt)", 
            height=150, 
            placeholder="请在此输入详细的提示词...\n【@功能提示】：下方上传图片后，会自动生成小巧的缩略图并标记为 @图1、@图2。您可以直接在文本中描述：“@图1 为男主角，@图2 作为视频首帧...”"
        )
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            ref_mode = st.selectbox("🎯 模式", [
                "0. 纯文生视频 (支持联网)",
                "1. 首帧生视频 (仅需1图)", 
                "2. 首尾帧生视频 (仅需2图)", 
                "3. 多模态参考 (角色+分镜)"
            ])
        with col2:
            model_type = st.selectbox("⚙️ 引擎", ["Seedance 2.0 (画质优先)", "Seedance 2.0 fast (速度优先)"])
        with col3:
            ratio = st.selectbox("📏 比例", ["自适应", "16:9", "9:16", "4:3", "3:4", "1:1", "21:9"])
        with col4:
            duration = st.selectbox("⏱️ 时长", ["5 秒", "8 秒", "10 秒", "15 秒", "智能决定 (-1)"])
        with col5:
            audio_opt = st.selectbox("🎵 声音", ["生成配套音效/配乐", "无声版"])
            
        st.write("---")
        
        allowed_types = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff']
        asset_input_1 = ""
        asset_input_2 = ""
        multi_assets = ""
        uploaded_file_1 = None
        uploaded_file_2 = None
        multi_uploads = []
        enable_web_search = False

        if ref_mode.startswith("0."):
            st.info("💡 纯文本生成模式。开启联网搜索可大幅提升实效性元素的准确度。")
            enable_web_search = st.toggle("🌐 开启联网增强搜索 (Web Search)")

        elif ref_mode.startswith("1."):
            col_a, col_b = st.columns(2)
            with col_a:
                asset_input_1 = st.text_input("🎭 官方 Asset ID (无则留空)")
            with col_b:
                uploaded_file_1 = st.file_uploader("🖼️ 或上传本地【首帧图】", type=allowed_types)
                if uploaded_file_1:
                    st.image(uploaded_file_1, caption="🏷️ @图1 (首帧)", width=150)

        elif ref_mode.startswith("2."):
            c1, c2 = st.columns(2)
            with c1: 
                asset_input_1 = st.text_input("🎭 首帧 Asset ID (无则留空)")
                uploaded_file_1 = st.file_uploader("🖼️ 或上传本地【首帧图】", type=allowed_types)
                if uploaded_file_1:
                    st.image(uploaded_file_1, caption="🏷️ @图1 (首帧)", width=150)
            with c2:
                asset_input_2 = st.text_input("🎭 尾帧 Asset ID (无则留空)")
                uploaded_file_2 = st.file_uploader("🖼️ 或上传本地【尾帧图】", type=allowed_types)
                if uploaded_file_2:
                    st.image(uploaded_file_2, caption="🏷️ @图2 (尾帧)", width=150)

        elif ref_mode.startswith("3."):
            st.success("🌟 高级混合模式：同时传入已过审的【角色 ID】和自绘的【本地分镜参考图】！")
            c1, c2 = st.columns(2)
            with c1:
                multi_assets = st.text_input("🎭 官方 Asset ID (多个用逗号隔开，无则留空)")
            with c2:
                multi_uploads = st.file_uploader("🖼️ 上传本地分镜图 (支持多选)", type=allowed_types, accept_multiple_files=True)
            
            if multi_uploads:
                st.markdown
