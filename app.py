import streamlit as st
import requests
import time
from supabase import create_client, Client

# ================= 1. 核心配置区 =================
# 从 Streamlit 保险箱读取钥匙 (绝对安全，代码里不再有明文密码)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Seedance API Token 也从保险箱读取
SEEDANCE_API_TOKEN = st.secrets["SEEDANCE_API_TOKEN"]

# ================= 2. 登录拦截系统 =================
# 初始化登录状态
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

# 如果没登录，就显示登录框
if not st.session_state["logged_in"]:
    st.markdown("<h2 style='text-align: center;'>🔐 魔方国际影业 - 内部系统</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        user_input = st.text_input("员工账号")
        pwd_input = st.text_input("登录密码", type="password")
        
        if st.button("登录系统", use_container_width=True):
            # 身份判断逻辑
            if user_input == "admin" and pwd_input == "888888":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "天九老板"
                st.session_state["role"] = "admin"
                st.rerun()
            elif user_input == "yuangong1" and pwd_input == "123456":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "剪辑师小王"
                st.session_state["role"] = "employee"
                st.rerun()
            elif user_input == "zhangsan" and pwd_input == "666888":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "特效师张三"
                st.session_state["role"] = "employee"
                st.rerun()
            else:
                st.error("账号或密码错误，请联系管理员！")
    st.stop() # 拦截器：没登录的人运行到这里就停止了，看不到下面的代码

# ================= 3. 登录后的侧边栏 =================
st.sidebar.title(f"👤 欢迎, {st.session_state['username']}")
st.sidebar.write(f"当前身份: {'超级管理员' if st.session_state['role'] == 'admin' else '内部员工'}")
st.sidebar.write("---")
if st.sidebar.button("退出登录"):
    st.session_state["logged_in"] = False
    st.rerun()

# ================= 4. 老板专属后台 (仅 Admin 可见) =================
if st.session_state["role"] == "admin":
    st.title("📊 魔方国际影业 - 财务与算力后台")
    st.write("这里记录了所有员工消耗的 Token 数据。")
    
    # 从 Supabase 拉取数据
    try:
        response = supabase.table("token_logs").select("*").order("created_at", desc=True).execute()
        logs = response.data
        if logs:
            st.dataframe(logs, use_container_width=True)
        else:
            st.info("目前还没有员工生成记录。")
    except Exception as e:
        st.error(f"连接数据库失败，请检查配置: {e}")

# ================= 5. 员工创作台 (Admin 和 员工均可见) =================
else:
    st.title("🎬 魔方国际影业 - Seedance 2.0 创作站")
    
    st.subheader("📝 创作面板")
    prompt = st.text_area("视频分镜提示词 (Prompt)", placeholder="例如：陆妄川站在洗灵池旁，剑气纵横...")
    uploaded_file = st.file_uploader("🖼️ 角色参考图上传 (严格遵守 V1.0 规则)", type=['png', 'jpg', 'jpeg'])
    
    st.write("---")
    if st.button("🚀 提交生成任务", use_container_width=True):
        if not prompt:
            st.warning("⚠️ 必须输入提示词才能生成！")
        else:
            with st.spinner("正在调用 Seedance 引擎，请稍候..."):
                # 这里是模拟 API 请求等待时间
                time.sleep(2) 
                
                # ======== 核心：生成完毕后，自动记账 ========
                try:
                    # 假设每次生成消耗 15 Token
                    supabase.table("token_logs").insert({
                        "employee_name": st.session_state["username"],
                        "action_type": "长生劫分镜生成",
                        "prompt_text": prompt,
                        "tokens_cost": 15
                    }).execute()
                    
                    st.success("🎉 视频生成任务已提交！Token 消耗已自动记录。")
                except Exception as e:
                    st.error(f"账本记录失败: {e}")
