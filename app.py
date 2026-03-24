import streamlit as st
import time
import requests
import base64
from supabase import create_client, Client
import extra_streamlit_components as stx

# ================= 1. 核心配置与 API 密钥 =================
st.set_page_config(page_title="魔方国际影业 - AI 创作站", page_icon="🎬", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SEEDANCE_API_TOKEN = st.secrets["SEEDANCE_API_TOKEN"]

# 真实的 Seedance API 接口地址
CREATE_URL = "http://118.196.64.1/api/v1/doubao/create" 
GET_URL = "http://118.196.64.1/api/v1/doubao/get_result" 

# ================= 2. 记忆芯片 (Cookie 自动登录) =================
# 【修复报错】：去掉缓存装饰器，直接使用固定 key 实例化
cookie_manager = stx.CookieManager(key="cookie_mgr")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["role"] = ""

# 尝试从 Cookie 读取登录状态
stored_user = cookie_manager.get(cookie="seedance_user")
stored_role = cookie_manager.get(cookie="seedance_role")

if stored_user and stored_role and not st.session_state["logged_in"]:
    st.session_state["logged_in"] = True
    st.session_state["username"] = stored_user
    st.session_state["role"] = stored_role

# 登录拦截界面
if not st.session_state["logged_in"]:
    st.markdown("<br><br><h2 style='text-align: center;'>🔐 魔方国际影业 - 内部系统</h2>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.info("💡 内部测试系统，请使用管理员分配的专属账号登录。")
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
                # 写入 Cookie
                cookie_manager.set("seedance_user", user_info["name"], max_age=30*24*3600)
                cookie_manager.set("seedance_role", user_info["role"], max_age=30*24*3600)
                time.sleep(1) # 给浏览器一点时间写入 Cookie
                st.rerun()
            else:
                st.error("⚠️ 账号或密码错误！")
    st.stop()

# ================= 3. 侧边栏 =================
st.sidebar.title(f"👤 {st.session_state['username']}")
st.sidebar.caption(f"当前身份: {'👑 超级管理员' if st.session_state['role'] == 'admin' else '💼 内部员工'}")

if st.sidebar.button("退出登录"):
    cookie_manager.delete("seedance_user")
    cookie_manager.delete("seedance_role")
    st.session_state["logged_in"] = False
    time.sleep(0.5)
    st.rerun()

# ================= 4. 老板后台 =================
if st.session_state["role"] == "admin":
    st.title("📊 财务与算力消耗控制台")
    try:
        response = supabase.table("token_logs").select("*").order("created_at", desc=True).execute()
        if response.data:
            st.dataframe(response.data, use_container_width=True)
        else:
            st.info("暂无生成记录。")
    except Exception as e:
        st.error(f"数据库连接失败: {e}")

# ================= 5. 员工真实创作台 =================
else:
    st.markdown("## 🎬 魔方国际影业 - Seedance 2.0 视频生成")
    
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
            audio_opt = st.selectbox("🎵 声音", ["生成配乐", "无声版"])
            
        st.write("---")
        
        # 动态上传区
        uploaded_first = None
        uploaded_last = None
        if ref_mode == "首帧生成":
            uploaded_first = st.file_uploader("🖼️ 上传参考首帧 (单图<30MB)", type=['png', 'jpg', 'jpeg'])
        elif ref_mode == "首尾帧生成":
            c1, c2 = st.columns(2)
            with c1: uploaded_first = st.file_uploader("🖼️ 上传【首帧】", type=['png', 'jpg', 'jpeg'])
            with c2: uploaded_last = st.file_uploader("🖼️ 上传【尾帧】", type=['png', 'jpg', 'jpeg'])

        # ======== 核心：真实 API 调用逻辑 (重构版) ========
        def encode_image(upload_file):
            if not upload_file: return None
            img_bytes = upload_file.getvalue()
            b64 = base64.b64encode(img_bytes).decode("utf-8")
            ext = upload_file.name.split('.')[-1].lower()
            if ext == 'jpg': ext = 'jpeg'
            return f"data:image/{ext};base64,{b64}"

        if st.button("🚀 提交真实生成任务", type="primary", use_container_width=True):
            if not prompt:
                st.warning("⚠️ 请先输入画面描述 (Prompt) 才能进行生成！")
            elif ref_mode == "首帧生成" and not uploaded_first:
                st.warning("⚠️ 此模式必须上传首帧图片！")
            elif ref_mode == "首尾帧生成" and (not uploaded_first or not uploaded_last):
                st.warning("⚠️ 此模式必须上传首尾两张图片！")
            else:
                status_box = st.info("⏳ 正在打包数据，请求云端引擎...")
                progress_bar = st.progress(10)
                
                # 1. 组装官方 API 参数
                ratio_val = "adaptive" if ratio == "自适应" else ratio
                dur_val = -1 if duration == "智能决定" else int(duration.split(" ")[0])
                audio_val = True if audio_opt == "生成配乐" else False
                
                # 【修复代码核心】：完全重构 payload 的组装方式，根据引擎和参考模式动态变化
                
                # 基础 Payload (基础参数和纯文本提示词)
                payload = {
                    "generate_audio": audio_val,
                    "ratio": ratio_val,
                    "duration": dur_val,
                    "content": [{"type": "text", "text": prompt}]
                }
                
                # 获取引擎类型
                is_fast = "fast" in model_type
                
                # 定义模型 ID (⚠️ 用户需要自行向 Seedance 更换为有效的ID)
                # 您之前的两个 ID 都报错不存在，请在这里更换为 Seedance 的有效 ID
                MODEL_ID_20 = "ep-20260307130721-bx7tv" # 【更换为有效的ID】：请联系 Seedance 更换，当前的 ep-20260307130721-bx7tv 报错不存在
                MODEL_ID_FAST = "ep-20260307130821-xw5wf" # 【更换为有效的ID】：请联系 Seedance 更换，当前的 ep-20260307130821-xw5wf 报错不存在

                # 在 ID 修复前，阻止代码运行，防止再次报错 InvalidParameter
                if MODEL_ID_20 == "ep-20260307130721-bx7tv" or MODEL_ID_FAST == "ep-20260307130821-xw5wf":
                    st.error("❌ 生成被阻止：代码中使用的 Seedance 模型 ID (ep_id) 已被 Seedance 标记为不存在或已过期。")
                    st.info("💡 请联系 Seedance 获取最新的'画质优先'和'速度优先'模型 ID，并在代码中标记了 `【更换为有效的ID】` 的位置进行更换。")
                    st.stop()

                payload["model"] = MODEL_ID_FAST if is_fast else MODEL_ID_20
                
                # 组装图片参考 (根据官方文档规范，不再错误地放在 content 中)
                img_b64_first = encode_image(uploaded_first)
                img_b64_last = encode_image(uploaded_last)
                
                if img_b64_first or img_b64_last:
                    # 逻辑 1: Seedance 2.0 (画质优先) 使用 image_reference 参数
                    if not is_fast:
                        payload["image_reference"] = {}
                        if img_b64_first:
                            payload["image_reference"]["first_frame_url"] = img_b64_first
                        if img_b64_last:
                            # 根据 Seedance 2.0 接口规范，不支持 last_frame_url 参数。
                            # 官方建议：如果是首尾帧模式，请将引擎切换为 [fast (速度优先)] 模式提交。
                            st.warning("⚠️ [画质优先] 引擎仅支持 [首帧生成]。我们将优先使用您的首帧图片。")
                            st.info("💡 如果您必须使用首尾帧模式，请在左侧将引擎切换为 [Seedance 2.0 fast (速度优先)] 模式提交。")
                    
                    # 逻辑 2: Seedance 2.0 fast (速度优先) 使用 all_to_all_reference 参数
                    else:
                        # 速度优先模式通过多图数组形式传递
                        images_array = []
                        if img_b64_first:
                            images_array.append({"url": img_b64_first})
                        if img_b64_last:
                            images_array.append({"url": img_b64_last})
                            
                        # 如果没有用首帧/尾帧上传框，但选了全能参考 (通过 accept_multiple_files 批量上传的，暂未做逻辑)
                        
                        payload["all_to_all_reference"] = {"image_reference": images_array}
                
                headers = {"Authorization": f"Bearer {SEEDANCE_API_TOKEN}", "Content-Type": "application/json"}
                
                try:
                    # 2. 发送创建任务请求
                    res = requests.post(CREATE_URL, headers=headers, json=payload).json()
                    task_id = res.get("id")
                    
                    if not task_id:
                        st.error(f"❌ 任务创建失败: {res}")
                        st.stop()
                        
                    status_box.info(f"✅ 任务投递成功！任务ID: {task_id}。正在排队渲染，请耐心等待...")
                    progress_bar.progress(30)
                    
                    # 3. 轮询获取结果
                    while True:
                        time.sleep(5) 
                        status_res = requests.post(GET_URL, headers=headers, json={"id": task_id}).json()
                        current_status = status_res.get("status")
                        
                        if current_status == "queued":
                            status_box.warning("🔄 引擎排队中，请稍候...")
                            progress_bar.progress(40)
                        elif current_status == "running":
                            status_box.info("🎨 算力全开，正在疯狂渲染视频帧...")
                            progress_bar.progress(70)
                        elif current_status == "succeeded":
                            progress_bar.progress(100)
                            status_box.success("🎉 生成大功告成！")
                            video_url = status_res.get("content", {}).get("video_url")
                            st.video(video_url) 
                            
                            # 记账
                            try:
                                tokens_used = status_res.get("usage", {}).get("completion_tokens", 15)
                                supabase.table("token_logs").insert({
                                    "employee_name": st.session_state["username"],
                                    "action_type": ref_mode,
                                    "prompt_text": prompt[:50],
                                    "tokens_cost": tokens_used
                                }).execute()
                            except: pass
                            break
                        elif current_status in ["failed", "cancelled", "expired"]:
                            status_box.error(f"❌ 生成失败，状态: {current_status}")
                            if "error" in status_res:
                                st.error(f"错误信息: {status_res['error'].get('message', '未知错误')}")
                            break
                            
                except Exception as e:
                    st.error(f"网络通信异常: {e}")
