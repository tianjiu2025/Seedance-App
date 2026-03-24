import streamlit as st
import time
from supabase import create_client, Client

# ================= 1. 核心配置区 =================
# 设置页面基本属性 (必须放在最前面，让页面更宽更好看)
st.set_page_config(page_title="魔方国际影业 - AI 创作站", page_icon="🎬", layout="wide")

# 从 Streamlit 保险箱读取钥匙 (绝对安全)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SEEDANCE_API_TOKEN = st.secrets["SEEDANCE_API_TOKEN"]

# ================= 2. 登录拦截系统 =================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

if not st.session_state["logged_in"]:
    st.markdown("<br><br><h2 style='text-align: center;'>🔐 魔方国际影业 - 内部系统</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.info("💡 内部测试系统，请使用管理员分配的专属账号登录。")
        user_input = st.text_input("👤 员工账号")
        pwd_input = st.text_input("🔑 登录密码", type="password")
        
        if st.button("🚀 登录系统", use_container_width=True):
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
                st.error("⚠️ 账号或密码错误，请核对后再试！")
    st.stop()

# ================= 3. 登录后的侧边栏 =================
st.sidebar.title(f"👤 {st.session_state['username']}")
st.sidebar.caption(f"当前身份: {'👑 超级管理员' if st.session_state['role'] == 'admin' else '💼 内部员工'}")
st.sidebar.write("---")

with st.sidebar.expander("📖 必读：素材提交规则 (V1.0)", expanded=True):
    st.markdown("""
    **【角色图片要求】**
    * **主旨**：以仿真人为主，必须清晰展示角色特征。
    * **数量**：单个角色 **最多3张**（正/侧/背）。
    * **规范**：至少1张完整正面图（看清脸），**不需要**任何配饰图解。
    * **红线**：严禁上传名人肖像（涉敏无法通过）。
    
    **【文件参数限制】**
    * **格式**：jpeg, png, webp, bmp, tiff, gif, heic
    * **比例/尺寸**：长宽比 0.4~2.5 之间；边长 300~6000 像素。
    * **大小**：单张图片不超过 **30 MB**。
    
    **【⚠️ 命名终极规范】**
    * **只能包含**：中文、字母、数字、下划线 `_`、短横线 `-`。
    * **严禁包含**：空格及其他特殊符号！
    * **长度**：最多 12 个字。
    """)

if st.sidebar.button("退出登录", type="primary"):
    st.session_state["logged_in"] = False
    st.rerun()

# ================= 4. 老板专属后台 (仅 Admin 可见) =================
if st.session_state["role"] == "admin":
    st.title("📊 财务与算力消耗控制台")
    st.write("欢迎回来，老板。以下是全公司 Seedance API 的调用与 Token 消耗记录。")
    
    try:
        response = supabase.table("token_logs").select("*").order("created_at", desc=True).execute()
        logs = response.data
        if logs:
            st.dataframe(logs, use_container_width=True)
        else:
            st.info("目前还没有员工提交过生成任务。")
    except Exception as e:
        st.error(f"连接数据库失败，请检查配置: {e}")

# ================= 5. 员工创作台 (Admin 和 员工均可见) =================
else:
    st.markdown("## 🎬 魔方国际影业 - 开启你的 视频生成 即刻造梦！")
    
    # 将主界面放在一个好看的卡片容器里
    with st.container(border=True):
        # 1. 提示词输入区
        prompt = st.text_area(
            "📝 画面描述 (Prompt)", 
            placeholder="输入文字，描述你想创作的画面内容、运动方式等。例如：陆妄川与江月白在洗灵池旁对峙，仙气缭绕，剑拔弩张...",
            height=120
        )
        
        # 2. 即梦风格的参数选择区
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            ref_mode = st.selectbox("🎯 参考模式", ["文生视频", "首帧生成", "首尾帧生成", "全能参考 (多模态)"])
        with col2:
            model_type = st.selectbox("⚙️ 引擎版本", ["Seedance 2.0 (画质优先)", "Seedance 2.0 fast (速度优先)"])
        with col3:
            ratio = st.selectbox("📏 画面比例", ["自适应 (Adaptive)", "16:9 (横屏)", "9:16 (竖屏)", "4:3", "3:4", "1:1", "21:9"])
        with col4:
            duration = st.selectbox("⏱️ 视频时长", ["5 秒", "4 秒", "8 秒", "10 秒", "15 秒", "模型智能决定"])
        with col5:
            audio_opt = st.selectbox("🎵 声音选项", ["生成配套音效/配乐", "无声纯净版"])
        
        st.write("---")
        
        # 3. 动态上传区 (根据模式自动变化)
        allowed_types = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'heic']
        
        if ref_mode == "文生视频":
            st.info("💡 当前为【文生视频】模式，模型将完全发挥想象力，无需上传参考图。")
            
        elif ref_mode == "首帧生成":
            st.markdown("#### 🖼️ 上传参考首帧")
            st.caption("⚠️ 文件名禁带空格，最多12字！单张<30MB。单角色最多传3张图（含1张正面）。")
            uploaded_first = st.file_uploader("拖拽图片到此处，或点击上传", type=allowed_types)
            
        elif ref_mode == "首尾帧生成":
            st.markdown("#### 🎞️ 上传首尾帧")
            st.caption("⚠️ 文件名禁带空格，最多12字！单张<30MB。单角色最多传3张图（含1张正面）。")
            c1, c2 = st.columns(2)
            with c1:
                uploaded_first = st.file_uploader("➕ 上传【首帧】图片", type=allowed_types)
            with c2:
                uploaded_last = st.file_uploader("➕ 上传【尾帧】图片", type=allowed_types)
                
        elif ref_mode == "全能参考 (多模态)":
            st.markdown("#### 🧩 上传综合参考素材 (图片/视频/音频)")
            st.caption("⚠️ 文件名禁带空格，最多12字！可上传场景参考、人物特征、指定音乐等。")
            uploaded_multi = st.file_uploader("支持批量拖拽多份素材（最多9张图、3个视频、3个音频）", accept_multiple_files=True)

        st.write("") # 留点空隙
        
        # 4. 提交按钮与生成逻辑
        if st.button("🚀 提交生成任务", type="primary", use_container_width=True):
            if not prompt:
                st.warning("⚠️ 请先输入画面描述 (Prompt) 才能进行生成！")
            else:
                # === 所见即所得：动态进度条展示 ===
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.markdown("⏳ **正在连接 Seedance 引擎...**")
                time.sleep(1)
                progress_bar.progress(30)
                
                status_text.markdown("⚙️ **正在分析规则与解析提示词...** (校验合法性)")
                time.sleep(1.5)
                progress_bar.progress(60)
                
                status_text.markdown("🎨 **算力全开，正在渲染分镜画面...** (这可能需要几分钟)")
                time.sleep(1.5)
                progress_bar.progress(90)
                
                status_text.markdown("🎞️ **正在进行最终合成与音效混流...**")
                time.sleep(1)
                progress_bar.progress(100)
                
                status_text.empty() # 清除状态文字
                
                # === 结果展示区 ===
                st.success("🎉 生成成功！请预览下方视频：")
                
                # 这是一个开源的占位测试视频，模拟真实的播放器效果
                st.video("https://www.w3schools.com/html/mov_bbb.mp4")
                
                # === 后台自动记账 ===
                try:
                    # 模拟智能扣费逻辑
                    cost = 15
                    if ref_mode == "全能参考 (多模态)": cost = 25
                    if duration == "15 秒": cost += 10
                    
                    supabase.table("token_logs").insert({
                        "employee_name": st.session_state["username"],
                        "action_type": f"{ref_mode} ({model_type})",
                        "prompt_text": prompt,
                        "tokens_cost": cost
                    }).execute()
                except Exception as e:
                    pass # 静默处理记账错误，不打扰员工使用
