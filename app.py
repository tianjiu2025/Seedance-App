import streamlit as st
import time
from supabase import create_client, Client

# ================= 1. 核心配置区 =================
# 从 Streamlit 保险箱读取钥匙 (绝对安全，代码里不再有明文密码)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
            # ================= 身份判断逻辑 =================
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
            elif user_input == "lisi" and pwd_input == "222222":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "原画师李四"
                st.session_state["role"] = "employee"
                st.rerun()
            elif user_input == "wangwu" and pwd_input == "333333":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "音效师王五"
                st.session_state["role"] = "employee"
                st.rerun()
            elif user_input == "zhaoliu" and pwd_input == "444444":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "模型师赵六"
                st.session_state["role"] = "employee"
                st.rerun()
            elif user_input == "sunqi" and pwd_input == "555555":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "动画师孙七"
                st.session_state["role"] = "employee"
                st.rerun()
            elif user_input == "zhouba" and pwd_input == "666666":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "编剧周八"
                st.session_state["role"] = "employee"
                st.rerun()
            elif user_input == "wujiu" and pwd_input == "777777":
                st.session_state["logged_in"] = True
                st.session_state["username"] = "运营吴九"
                st.session_state["role"] = "employee"
                st.rerun()
            else:
                st.error("账号或密码错误，请联系管理员！")
    st.stop() # 拦截器：没登录的人运行到这里就停止了

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
    prompt = st.text_area(
        "视频分镜提示词 (Prompt)", 
        placeholder="例如：陆妄川与江月白在洗灵池旁对峙，仙气缭绕，剑拔弩张..."
    )
    uploaded_file = st.file_uploader("🖼️ 角色参考图上传 (最高 4K 分辨率，无多余配饰)", type=['png', 'jpg', 'jpeg'])
    
    st.write("---")
    
    # 点击生成按钮后的逻辑
    if st.button("🚀 提交生成任务", use_container_width=True):
        if not prompt:
            st.warning("⚠️ 必须输入提示词才能生成视频！")
        else:
            # === 所见即所得：动态进度条展示 ===
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("⏳ 正在连接 Seedance 引擎...")
            time.sleep(1)
            progress_bar.progress(30)
            
            status_text.text("⚙️ 正在解析提示词与角色参考图...")
            time.sleep(1.5)
            progress_bar.progress(60)
            
            status_text.text("🎨 正在渲染分镜画面...")
            time.sleep(1.5)
            progress_bar.progress(90)
            
            status_text.text("🎞️ 正在合成最终视频序列...")
            time.sleep(1)
            progress_bar.progress(100)
            
            status_text.empty() # 清除状态文字
            
            # === 结果展示区 ===
            st.success("🎉 视频生成成功！(当前为演示播放器，待接入真实 API 后将显示实际视频)")
            
            # 这是一个开源的占位测试视频，让员工看到真实的播放器界面
            st.video("https://www.w3schools.com/html/mov_bbb.mp4")
            
            # === 后台自动记账 ===
            try:
                # 假设每次生成消耗 15 Token
                supabase.table("token_logs").insert({
                    "employee_name": st.session_state["username"],
                    "action_type": "分镜视频生成",
                    "prompt_text": prompt,
                    "tokens_cost": 15
                }).execute()
            except Exception as e:
                st.error(f"账本记录失败: {e}")
