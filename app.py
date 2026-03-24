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
                st.session_state["role"] = user_info["role"]
                
                cookie_manager.set("mgr_user", user_info["name"], max_age=30*24*3600)
                cookie_manager.set("mgr_role", user_info["role"], max_age=30*24*3600)
                time.sleep(1) 
                st.rerun()
            else:
                st.error("⚠️ 账号或密码错误！")
    st.stop()

# ================= 3. 侧边栏 =================
st.sidebar.title(f"👤 {st.session_state['username']}")
st.sidebar.caption(f"当前身份: {'👑 超级管理员' if st.session_state['role'] == 'admin' else '💼 内部员工'}")
if st.sidebar.button("退出登录"):
    cookie_manager.delete("mgr_user")
    cookie_manager.delete("mgr_role")
    st.session_state["logged_in"] = False
    st.rerun()

# ================= 4. 老板后台 =================
if st.session_state["role"] == "admin":
    st.title("📊 财务与算力控制台")
    try:
        response = supabase.table("token_logs").select("*").order("created_at", desc=True).execute()
        if response.data: st.dataframe(response.data, use_container_width=True)
        else: st.info("暂无生成记录。")
    except Exception as e: st.error(f"数据库连接失败: {e}")

# ================= 5. 员工真实创作台 =================
else:
    st.markdown("## 🎬 魔方国际影业 - Seedance 2.0 视频生成台")
    
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
        
        uploaded_first = None
        uploaded_last = None
        allowed_types = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff', 'heic']

        if ref_mode == "首帧生成":
            uploaded_first = st.file_uploader("🖼️ 上传参考【首帧】图", type=allowed_types)
        elif ref_mode == "首尾帧生成":
            c1, c2 = st.columns(2)
            with c1: uploaded_first = st.file_uploader("🖼️ 上传参考【首帧】图", type=allowed_types)
            with c2: uploaded_last = st.file_uploader("🖼️ 上传参考【尾帧】图", type=allowed_types)

        def encode_image(upload_file):
            if not upload_file: return None
            ext = upload_file.name.split('.')[-1].lower()
            if ext == 'jpg': ext = 'jpeg'
            img_bytes = upload_file.getvalue()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            return f"data:image/{ext};base64,{b64}"

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
                
                is_fast = "fast" in model_type
                # 直接使用官方文档提供的正确 ID
                model_id = "ep-20260307130821-xw5wf" if is_fast else "ep-20260307130721-bx7tv"
                
                ratio_val = "adaptive" if ratio == "自适应" else ratio
                dur_val = -1 if duration == "智能决定" else int(duration.split(" ")[0])
                audio_val = True if audio_opt == "生成配套音效/配乐" else False
                
                # API V2.5 规范：基本参数与 content 并列
                payload = {
                    "model": model_id,
                    "content": [{"type": "text", "text": prompt}],
                    "generate_audio": audio_val,
                    "ratio": ratio_val,
                    "duration": dur_val
                }
                
                img_b64_first = encode_image(uploaded_first)
                img_b64_last = encode_image(uploaded_last)
                
                if img_b64_first or img_b64_last:
                    if not is_fast:
                        # 画质优先引擎：使用 image_reference
                        img_ref = {}
                        if img_b64_first: img_ref["first_frame_url"] = img_b64_first
                        if img_b64_last: img_ref["last_frame_url"] = img_b64_last
                        payload["image_reference"] = img_ref
                    else:
                        # 速度优先引擎：使用 all_to_all_reference
                        images_array = []
                        if img_b64_first: images_array.append({"url": img_b64_first})
                        if img_b64_last: images_array.append({"url": img_b64_last})
                        payload["all_to_all_reference"] = {"image_reference": images_array}
                
                headers = {"Authorization": f"Bearer {SEEDANCE_API_TOKEN}", "Content-Type": "application/json"}
                
                try:
                    res = requests.post(CREATE_URL, headers=headers, json=payload)
                    if res.status_code != 200:
                        log_api_error(f"❌ 任务投递失败：HTTP {res.status_code} - 响应：{res.text}")
                        st.stop()
                        
                    create_res_json = res.json()
                    task_id = create_res_json.get("id")
                    
                    if not task_id:
                        log_api_error(f"❌ 任务投递失败（API无ID）：{create_res_json}")
                        st.stop()
                        
                    status_box.info(f"✅ 任务投递成功！任务ID: {task_id}。正在排队渲染，请耐心等待...")
                    progress_bar.progress(30)
                    
                    retry_count = 0
                    while retry_count < 100: 
                        time.sleep(10) 
                        retry_count += 1
                        
                        try:
                            status_res = requests.post(GET_URL, headers=headers, json={"id": task_id})
                            if status_res.status_code != 200: continue 
                            
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
                                
                                try:
                                    tokens_used = status_res_json.get("usage", {}).get("completion_tokens", 15)
                                    supabase.table("token_logs").insert({
                                        "employee_name": st.session_state["username"],
                                        "action_type": ref_mode,
                                        "prompt_text": prompt[:50], 
                                        "tokens_cost": tokens_used
                                    }).execute()
                                except: pass 
                                break
                            elif current_status in ["failed", "cancelled", "expired"]:
                                log_api_error(f"❌ 生成失败，状态: {current_status}")
                                break
                        except Exception as poll_e:
                            log_api_error(f"⚠️ 轮询过程出现异常，系统正在自动重试: {poll_e}")
                            
                except Exception as e:
                    log_api_error(f"网络通信出现严重故障，请稍后再试：{e}")
