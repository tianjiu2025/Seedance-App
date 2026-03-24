import streamlit as st
import time
import requests
import base64
import json
from supabase import create_client, Client
import extra_streamlit_components as stx

# ================= 1. 核心配置与 API 密钥 =================
st.set_page_config(page_title="魔方国际影业 - AI 创作站", page_icon="🎬", layout="wide")

# 配置错误排查日志 (如果是 Public 部署，日志在 Streamlit 控制台看)
def log_api_error(msg):
    st.error(msg)
    # st.sidebar.error(msg) # 调试时可选在侧边栏也显示

# 从保险箱读取配置 (⚠️ 请确保 Secrets 已按需配置)
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    SEEDANCE_API_TOKEN = st.secrets["SEEDANCE_API_TOKEN"]
    # V2.5 新版接口地址 (通常和 V1 是一样的，只是后台升级了 V2.5 逻辑)
    CREATE_URL = st.secrets.get("CREATE_URL", "http://118.196.64.1/api/v1/doubao/create") 
    GET_URL = st.secrets.get("GET_URL", "http://118.196.64.1/api/v1/doubao/get_result") 
except Exception as e:
    st.error(f"❌ 必填 Secrets 配置缺失: {e}")
    st.stop()

# ================= 2. 记忆芯片与登录逻辑 =================
# 你之前的 Cookie 记忆和登录逻辑代码 (yuangong1, zhangsan... admin 等)
# 此处为了不泄露你 TXT 文件的数据，我使用简化的通用登录代码代替，
# 请务必自行替换回你之前使用的、完整的全员账号密码逻辑！

cookie_manager = stx.CookieManager(key="mofang_mgr")
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

# 尝试从 Cookie 读取
stored_user = cookie_manager.get(cookie="mgr_user")
stored_role = cookie_manager.get(cookie="mgr_role")

if stored_user and stored_role and not st.session_state["logged_in"]:
    st.session_state["logged_in"] = True
    st.session_state["username"] = stored_user
    st.session_state["role"] = stored_role

# 登录拦截 (通用账号，替换为您自己的逻辑)
if not st.session_state["logged_in"]:
    st.markdown("<br><br><h2 style='text-align: center;'>🔐 魔方国际影业 - 内部系统</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        user_input = st.text_input("👤 员工账号")
        pwd_input = st.text_input("🔑 登录密码", type="password")
        if st.button("🚀 登录系统", use_container_width=True):
            if user_input == "admin" and pwd_input == "888888":
                name, role = "天九老板", "admin"
            elif user_input == "test" and pwd_input == "123456": # 测试员工
                name, role = "测试人员", "employee"
            else:
                st.error("⚠️ 账号或密码错误！")
                st.stop()
            
            st.session_state["logged_in"] = True
            st.session_state["username"] = name
            st.session_state["role"] = role
            cookie_manager.set("mgr_user", name, max_age=30*24*3600)
            cookie_manager.set("mgr_role", role, max_age=30*24*3600)
            time.sleep(0.5)
            st.rerun()
    st.stop()

# ================= 3. 侧边栏 =================
st.sidebar.title(f"👤 {st.session_state['username']}")
if st.sidebar.button("退出登录"):
    cookie_manager.delete("mgr_user")
    cookie_manager.delete("mgr_role")
    st.session_state["logged_in"] = False
    st.rerun()

# ================= 4. 老板后台 ( Admin 专属) =================
if st.session_state["role"] == "admin":
    st.title("📊 财务与算力控制台")
    try:
        response = supabase.table("token_logs").select("*").order("created_at", desc=True).execute()
        if response.data: st.dataframe(response.data, use_container_width=True)
    except Exception as e: st.error(f"数据库连接失败: {e}")

# ================= 5. 员工真实创作台 (重要修改区) =================
else:
    st.markdown("## 🎬 魔方国际影业 - Seedance 2.0 视频生成台")
    
    # 将旧的 rules.docx 逻辑展示在 expando 里
    with st.expander("📖 必读：素材提交规则 (V1.0 精炼版)", expanded=True):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown("""
            **【角色图片要求】**
            * 仿真人为主，特征清晰。单个角色**最多3张图**（正/侧/背）。
            * **严禁**上传名人肖像（涉敏无法通过）。
            """)
        with col_r2:
            st.markdown("""
            **【文件与命名要求】**
            * jpeg, png, heic 等。长宽比 0.4~2.5。单张<30MB。
            * **⚠️ 命名必须干净**：只能包含中文、字母、数字、`_`、`-`。
            * **严禁包含空格及其他符号！**。
            """)

    with st.container(border=True):
        prompt = st.text_area("📝 画面描述 (Prompt)", height=100)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            ref_mode = st.selectbox("🎯 模式", ["文生视频", "首帧生成", "首尾帧生成"])
        with col2:
            model_type = st.selectbox("⚙️ 引擎", ["Seedance 2.0 (画质优先)", "Seedance 2.0 fast (速度优先)"])
        with col3:
            ratio = st.selectbox("📏 比例", ["自适应", "16:9", "9:16", "4:3", "3:4", "1:1", "21:9"])
        with col4:
            duration = st.selectbox("⏱️ 时长", ["5 秒", "8 秒", "10 秒", "15 秒", "智能决定"])
        with col5:
            audio_opt = st.selectbox("🎵 声音", ["生成配套音效/配乐", "无声版"])
            
        st.write("---")
        
        # 动态上传区
        uploaded_first = None
        uploaded_last = None
        allowed_types = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'heic']

        if ref_mode == "首帧生成":
            uploaded_first = st.file_uploader("🖼️ 上传参考【首帧】图", type=allowed_types)
        elif ref_mode == "首尾帧生成":
            c1, c2 = st.columns(2)
            with c1: uploaded_first = st.file_uploader("🖼️ 上传参考【首帧】图", type=allowed_types)
            with c2: uploaded_last = st.file_uploader("🖼️ 上传参考【尾帧】图", type=allowed_types)

        # Base64 编码函数
        def encode_image(upload_file):
            if not upload_file: return None
            # 文档规范：jpeg, png, heic
            ext = upload_file.name.split('.')[-1].lower()
            if ext == 'jpg': ext = 'jpeg'
            
            # 这里添加根据 rules.docx 命名的校验逻辑（可选）
            
            img_bytes = upload_file.getvalue()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            return f"data:image/{ext};base64,{b64}"

        # ======== 核心：【彻底重构】符合 API V2.5 规范的真实逻辑 ========
        if st.button("🚀 提交真实生成任务", type="primary", use_container_width=True):
            if not prompt:
                st.warning("⚠️ 请输入画面描述 (Prompt) 才能进行生成！")
            elif ref_mode == "首帧生成" and not uploaded_first:
                st.warning("⚠️ 此模式必须上传首帧图片！")
            elif ref_mode == "首尾帧生成" and (not uploaded_first or not uploaded_last):
                st.warning("⚠️ 此模式必须上传首尾两张图片！")
            else:
                status_box = st.info("⏳ 正在打包数据，请求云端引擎...")
                progress_bar = st.progress(10)
                
                # 1. 组装符合文档规范的参数
                model_id = "ep-20260307130721-bx7tv" if "画质" in model_type else "ep-20260307130821-xw5wf"
                ratio_val = "adaptive" if ratio == "自适应" else ratio
                dur_val = -1 if duration == "智能决定" else int(duration.split(" ")[0])
                audio_val = True if audio_opt == "生成配套音效/配乐" else False
                
                # 【修改逻辑的核心】：根据文档第2页，将参考图参数移出 content，移到顶级参数位置！
                # 标准 content 数组
                api_content = [{"type": "text", "text": prompt}]
                
                # 构建 Payload
                payload = {
                    "model": model_id,
                    "content": api_content,
                    "generate_audio": audio_val,
                    "ratio": ratio_val,
                    "duration": dur_val
                }
                
                # 检查是否使用了图片参考模式
                img_b64_first = encode_image(uploaded_first)
                img_b64_last = encode_image(uploaded_last)
                
                if img_b64_first or img_b64_last:
                    # 获取引擎类型（画质优先 vs 速度优先 fast）
                    is_fast = "fast" in model_type
                    
                    # 逻辑 1: Seedance 2.0 (画质优先) 使用 image_reference 参数
                    if not is_fast:
                        img_ref = {}
                        if img_b64_first:
                            img_ref["first_frame_url"] = img_b64_first
                        if img_b64_last:
                            img_ref["last_frame_url"] = img_b64_last
                            
                        # V2.5 规范：放在顶级参数，与 content 并列
                        payload["image_reference"] = img_ref
                    
                    # 逻辑 2: Seedance 2.0 fast (速度优先) 使用 all_to_all_reference 参数
                    else:
                        # 快模型通过多图数组传递
                        images_array = []
                        if img_b64_first:
                            images_array.append({"url": img_b64_first})
                        if img_b64_last:
                            images_array.append({"url": img_b64_last})
                            
                        # V2.5 规范：放在顶级参数，与 content 并列
                        payload["all_to_all_reference"] = {"image_reference": images_array}
                
                # 调试用：将 JSON payload 打印到控制台或界面上供排查
                # st.json(payload) 

                headers = {"Authorization": f"Bearer {SEEDANCE_API_TOKEN}", "Content-Type": "application/json"}
                
                try:
                    # 2. 发送任务投递请求
                    res = requests.post(CREATE_URL, headers=headers, json=payload)
                    # 先检查 HTTP 错误代码
                    if res.status_code != 200:
                        log_api_error(f"❌ 任务投递失败：HTTP {res.status_code} - 响应：{res.text}")
                        st.stop()
                        
                    create_res_json = res.json()
                    task_id = create_res_json.get("id")
                    
                    if not task_id:
                        log_api_error(f"❌ 任务投递失败（API无ID）：{create_res_json}")
                        st.stop()
                        
                    # 投递成功后的逻辑保持不变
                    status_box.info(f"✅ 任务投递成功！任务ID: {task_id}。正在排队渲染，请耐心等待...")
                    progress_bar.progress(30)
                    
                    # 3. 轮询获取结果 (逻辑不变)
                    retry_count = 0
                    while retry_count < 100: # 轮询安全上限 (几分钟)
                        time.sleep(10) # 建议轮询间隔提高到 10s，减少网络压力
                        retry_count += 1
                        
                        try:
                            status_res = requests.post(GET_URL, headers=headers, json={"id": task_id})
                            if status_res.status_code != 200: continue # 临时故障忽略
                            
                            status_res_json = status_res.json()
                            current_status = status_res_json.get("status")
                            
                            if current_status == "queued":
                                status_box.warning(f"🔄 引擎排队中 (第 {retry_count} 次查询)...")
                                progress_bar.progress(40)
                            elif current_status == "running":
                                status_box.info("🎨 算力全开，正在疯狂渲染视频帧...")
                                progress_bar.progress(70)
                            elif current_status == "succeeded":
                                progress_bar.progress(100)
                                status_box.success("🎉 生成大功告成！")
                                video_url = status_res_json.get("content", {}).get("video_url")
                                st.video(video_url) 
                                
                                # 记账代码维持原有逻辑
                                try:
                                    tokens_used = status_res_json.get("usage", {}).get("completion_tokens", 15)
                                    supabase.table("token_logs").insert({
                                        "employee_name": st.session_state["username"],
                                        "action_type": ref_mode,
                                        "prompt_text": prompt[:50], # 缩减保存
                                        "tokens_cost": tokens_used
                                    }).execute()
                                except: pass # 静默处理记账错误
                                break
                            elif current_status in ["failed", "cancelled", "expired"]:
                                log_api_error(f"❌ 生成失败，状态: {current_status}")
                                break
                        exceptException as poll_e:
                            log_api_error(f"⚠️ 轮询过程出现异常，系统正在自动重试: {poll_e}")
                            
                except Exception as e:
                    log_api_error(f"网络通信出现严重故障，请稍后再试：{e}")
