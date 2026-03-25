import streamlit as st
import time
import requests
import base64
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
                "yuangong1": {"pwd": "123456", "name": "剪辑师小王", "role": "employee"}
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

    with st.container(border=True):
        prompt = st.text_area(
            "📝 画面描述 (Prompt)", 
            height=150, 
            placeholder="请在此输入详细的视频分镜描述...\n例如：镜头从远景拉近，陆妄川与江月白在洗灵池旁对峙。仙气缭绕，剑拔弩张..."
        )
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            # 核心更新 1：严格对齐 API 场景的模式分类
            ref_mode = st.selectbox("🎯 模式", [
                "文生视频 (纯文本)", 
                "多模态参考 (文+参考图)", 
                "图生视频 (首帧)", 
                "图生视频 (首尾帧)"
            ])
        with col2:
            model_type = st.selectbox("⚙️ 引擎", ["Seedance 2.0 (画质优先)", "Seedance 2.0 fast (速度优先)"])
        with col3:
            ratio = st.selectbox("📏 比例", ["自适应", "16:9", "9:16", "4:3", "3:4", "1:1", "21:9"])
        with col4:
            duration = st.selectbox("⏱️ 时长", ["5 秒", "8 秒", "10 秒", "15 秒", "智能决定"])
        with col5:
            audio_opt = st.selectbox("🎵 声音", ["生成配套音效/配乐", "无声版"])
            
        st.write("---")
        
        # ==========================================
        # 核心更新 2：规范化图片上传与 Base64 转换逻辑
        # ==========================================
        allowed_types = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff']
        
        def process_image_to_payload(url_input, upload_file, role):
            """将图片输入转换为 API 要求的字典格式"""
            if url_input and url_input.strip():
                return {"type": "image_url", "image_url": {"url": url_input.strip()}, "role": role}
            
            if upload_file:
                # 检查单张图片大小 (文档要求 < 30MB)
                if upload_file.size > 30 * 1024 * 1024:
                    st.error(f"图片 {upload_file.name} 超过 30MB 限制！请压缩后重试。")
                    st.stop()
                    
                ext = upload_file.name.split('.')[-1].lower()
                if ext == 'jpg': ext = 'jpeg'
                img_bytes = upload_file.getvalue()
                b64 = base64.b64encode(img_bytes).decode("utf-8")
                base64_url = f"data:image/{ext};base64,{b64}"
                return {"type": "image_url", "image_url": {"url": base64_url}, "role": role}
            
            return None

        # 用于存储最终要发送给大模型的 content 列表
        api_content = []
        if prompt.strip():
            api_content.append({"type": "text", "text": prompt.strip()})

        # 根据不同模式，动态渲染上传组件
        if ref_mode == "多模态参考 (文+参考图)":
            st.info("💡 多模态参考：您可以上传 1~9 张参考图片，模型会提取图片风格和元素。提示词是必填项。")
            ref_urls = st.text_input("🌐 网络参考图链接 (多个链接请用逗号英文 ',' 隔开)")
            ref_files = st.file_uploader("🖼️ 或上传本地参考图 (最多9张)", type=allowed_types, accept_multiple_files=True)
            
            # 处理多图逻辑
            if ref_urls:
                for url in ref_urls.split(','):
                    if url.strip():
                        api_content.append(process_image_to_payload(url.strip(), None, "reference_image"))
            if ref_files:
                for f in ref_files[:9]: # 强制截断最多9张
                    api_content.append(process_image_to_payload(None, f, "reference_image"))

        elif ref_mode == "图生视频 (首帧)":
            first_url = st.text_input("🌐 粘贴【首帧】网络图片链接")
            uploaded_first = st.file_uploader("🖼️ 或上传本地【首帧】参考图", type=allowed_types)
            img_payload = process_image_to_payload(first_url, uploaded_first, "first_frame")
            if img_payload:
                api_content.append(img_payload)

        elif ref_mode == "图生视频 (首尾帧)":
            c1, c2 = st.columns(2)
            with c1: 
                first_url = st.text_input("🌐 粘贴【首帧】网络链接")
                uploaded_first = st.file_uploader("🖼️ 或上传本地【首帧】", type=allowed_types)
                first_payload = process_image_to_payload(first_url, uploaded_first, "first_frame")
                if first_payload: api_content.append(first_payload)
            with c2:
                last_url = st.text_input("🌐 粘贴【尾帧】网络链接")
                uploaded_last = st.file_uploader("🖼️ 或上传本地【尾帧】", type=allowed_types)
                last_payload = process_image_to_payload(last_url, uploaded_last, "last_frame")
                if last_payload: api_content.append(last_payload)

        # 提交按钮
        if st.button("🚀 提交真实生成任务", type="primary", use_container_width=True):
            
            # 前置参数校验
            if ref_mode in ["文生视频 (纯文本)", "多模态参考 (文+参考图)"] and not prompt:
                st.warning("⚠️ 此模式下，必须输入画面描述 (Prompt)！")
                st.stop()
                
            if ref_mode == "图生视频 (首帧)" and len([c for c in api_content if c.get("role") == "first_frame"]) == 0:
                st.warning("⚠️ 请提供首帧图片！")
                st.stop()
                
            if ref_mode == "图生视频 (首尾帧)":
                has_first = any(c.get("role") == "first_frame" for c in api_content)
                has_last = any(c.get("role") == "last_frame" for c in api_content)
                if not (has_first and has_last):
                    st.warning("⚠️ 必须同时提供【首帧】和【尾帧】两张图片！")
                    st.stop()

            status_box = st.info("⏳ 正在组装原生请求体，直接投递给云端引擎...")
            progress_bar = st.progress(10)
            
            is_fast = "fast" in model_type
            model_id = "ep-20260307130821-xw5wf" if is_fast else "ep-20260307130721-bx7tv"
            
            ratio_val = "adaptive" if ratio == "自适应" else ratio
            dur_val = -1 if duration == "智能决定" else int(duration.split(" ")[0])
            audio_val = True if audio_opt == "生成配套音效/配乐" else False
            
            payload = {
                "model": model_id,
                "content": api_content,
                "generate_audio": audio_val,
                "ratio": ratio_val,
                "duration": dur_val
            }
            
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
                    
                status_box.info(f"✅ 任务投递成功！任务ID: {task_id}。引擎接收无误，正在渲染中...")
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
                                    "prompt_text": prompt[:50] if prompt else "无文本", 
                                    "tokens_cost": tokens_used
                                }).execute()
                            except: pass 
                            break
                        elif current_status in ["failed", "cancelled", "expired"]:
                            err_info = status_res_json.get("error")
                            if err_info and isinstance(err_info, dict):
                                err_msg = err_info.get("message", "未知原因")
                                err_code = err_info.get("code", "未知错误码")
                                log_api_error(f"❌ 引擎渲染失败 (状态: {current_status})\n\n原因: {err_msg} (错误码: {err_code})")
                            else:
                                log_api_error(f"❌ 引擎渲染失败 (状态: {current_status})\n\nAPI 未返回具体错误信息。")
                            break
                            
                    except Exception as poll_e:
                        log_api_error(f"⚠️ 轮询过程出现异常，系统正在自动重试: {poll_e}")
                        
            except Exception as e:
                log_api_error(f"网络通信出现严重故障，请稍后再试：{e}")
