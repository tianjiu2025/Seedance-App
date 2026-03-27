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
    st.rerun()

if st.session_state["role"] == "admin":
    st.title("📊 财务与算力控制台")
    try:
        response = supabase.table("token_logs").select("*").order("created_at", desc=True).execute()
        if response.data: st.dataframe(response.data, use_container_width=True)
        else: st.info("暂无生成记录。")
    except Exception as e: st.error(f"数据库连接失败: {e}")

# ================= 4. 员工真实创作台 (严格适配 V2.6) =================
else:
    st.markdown("## 🎬 魔方国际影业 - Seedance 2.0 视频生成台")

    with st.container(border=True):
        prompt = st.text_area(
            "📝 画面描述 (Prompt)", 
            height=150, 
            placeholder="请在此输入详细的提示词...\n【@功能提示】：当您在下方上传参考图后，系统会自动标记为 @图1、@图2。您可以直接在文本中描述：“@图1 为男主角，@图2 作为视频首帧...”"
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

        if ref_mode == "0. 纯文生视频 (支持联网)":
            st.info("💡 纯文本生成模式。开启联网搜索可大幅提升实效性元素的准确度。")
            enable_web_search = st.toggle("🌐 开启联网增强搜索 (Web Search)")

        elif ref_mode == "1. 首帧生视频 (仅需1图)":
            col_a, col_b = st.columns(2)
            with col_a:
                asset_input_1 = st.text_input("🎭 填入官方 Asset ID (如: asset-xxx)")
            with col_b:
                uploaded_file_1 = st.file_uploader("🖼️ 或上传本地【首帧图】(自动存入图床)", type=allowed_types)
                if uploaded_file_1:
                    st.image(uploaded_file_1, caption="🏷️ @图1 (首帧)", use_container_width=True)

        elif ref_mode == "2. 首尾帧生视频 (仅需2图)":
            c1, c2 = st.columns(2)
            with c1: 
                asset_input_1 = st.text_input("🎭 首帧 Asset ID")
                uploaded_file_1 = st.file_uploader("🖼️ 或上传本地【首帧图】", type=allowed_types)
                if uploaded_file_1:
                    st.image(uploaded_file_1, caption="🏷️ @图1 (首帧)", use_container_width=True)
            with c2:
                asset_input_2 = st.text_input("🎭 尾帧 Asset ID")
                uploaded_file_2 = st.file_uploader("🖼️ 或上传本地【尾帧图】", type=allowed_types)
                if uploaded_file_2:
                    st.image(uploaded_file_2, caption="🏷️ @图2 (尾帧)", use_container_width=True)

        elif ref_mode == "3. 多模态参考 (角色+分镜)":
            st.success("🌟 高级混合模式：同时传入已过审的【角色 ID】和自绘的【本地分镜参考图】！")
            c1, c2 = st.columns(2)
            with c1:
                multi_assets = st.text_input("🎭 填入角色 Asset ID (多个用英文逗号 , 隔开)")
            with c2:
                multi_uploads = st.file_uploader("🖼️ 上传分镜参考图 (支持多选，自动存入私有图床)", type=allowed_types, accept_multiple_files=True)
            
            if multi_uploads:
                st.markdown("### 📎 待引用的本地图库 (@图库)")
                cols = st.columns(min(len(multi_uploads), 4))
                for idx, up_file in enumerate(multi_uploads):
                    col_idx = idx % 4
                    with cols[col_idx]:
                        st.image(up_file, caption=f"🏷️ @图{idx+1}", use_container_width=True)

        def upload_to_supabase(upload_file):
            if not upload_file: return None
            try:
                ext = upload_file.name.split('.')[-1].lower()
                if ext == 'jpg': ext = 'jpeg'
                file_name = f"{uuid.uuid4().hex}.{ext}"
                file_bytes = upload_file.getvalue()
                
                supabase.storage.from_("assets").upload(
                    file=file_bytes,
                    path=file_name,
                    file_options={"content-type": f"image/{ext}"}
                )
                return supabase.storage.from_("assets").get_public_url(file_name)
            except Exception as e:
                st.error(f"⚠️ 自动上传图床失败，请检查 Supabase 存储桶设置！错误: {e}")
                return None

        def format_asset_id(val):
            val = val.strip()
            if not val.startswith("asset://"):
                val = f"asset://{val}"
            return val

        if st.button("🚀 提交真实生成任务", type="primary", use_container_width=True):
            if not prompt:
                st.warning("⚠️ 请输入画面描述 (Prompt) 才能进行生成！")
                st.stop()

            status_box = st.info("☁️ 正在打包素材并上传图床...")
            progress_bar = st.progress(5)
            
            api_content = [{"type": "text", "text": prompt}]
            
            if ref_mode == "1. 首帧生视频 (仅需1图)":
                if not asset_input_1 and not uploaded_file_1:
                    st.warning("⚠️ 此模式请提供 Asset ID 或上传一张本地图片！")
                    st.stop()
                final_url = format_asset_id(asset_input_1) if asset_input_1 else upload_to_supabase(uploaded_file_1)
                if not final_url: st.stop()
                api_content.append({"type": "image_url", "image_url": {"url": final_url}, "role": "first_frame"})

            elif ref_mode == "2. 首尾帧生视频 (仅需2图)":
                if (not asset_input_1 and not uploaded_file_1) or (not asset_input_2 and not uploaded_file_2):
                    st.warning("⚠️ 此模式请确保首尾两张图均已提供！")
                    st.stop()
                final_url_1 = format_asset_id(asset_input_1) if asset_input_1 else upload_to_supabase(uploaded_file_1)
                final_url_2 = format_asset_id(asset_input_2) if asset_input_2 else upload_to_supabase(uploaded_file_2)
                if not final_url_1 or not final_url_2: st.stop()
                api_content.append({"type": "image_url", "image_url": {"url": final_url_1}, "role": "first_frame"})
                api_content.append({"type": "image_url", "image_url": {"url": final_url_2}, "role": "last_frame"})

            elif ref_mode == "3. 多模态参考 (角色+分镜)":
                if not multi_assets and not multi_uploads:
                    st.warning("⚠️ 此模式请至少提供一个角色 ID 或上传一张参考图！")
                    st.stop()
                if multi_assets:
                    id_list = [x.strip() for x in multi_assets.split(",") if x.strip()]
                    for a_id in id_list:
                        api_content.append({"type": "image_url", "image_url": {"url": format_asset_id(a_id)}, "role": "reference_image"})
                if multi_uploads:
                    for up_file in multi_uploads:
                        up_url = upload_to_supabase(up_file)
                        if up_url:
                            api_content.append({"type": "image_url", "image_url": {"url": up_url}, "role": "reference_image"})

            status_box.info("⏳ 素材处理完毕！正在请求云端引擎...")
            progress_bar.progress(15)
            
            is_fast = "fast" in model_type
            model_id = "ep-20260307130821-xw5wf" if is_fast else "ep-20260307130721-bx7tv"
            ratio_val = "adaptive" if ratio == "自适应" else ratio
            dur_val = -1 if "智能决定" in duration else int(duration.split(" ")[0])
            audio_val = True if audio_opt == "生成配套音效/配乐" else False
            
            payload = {
                "model": model_id,
                "content": api_content,
                "generate_audio": audio_val,
                "ratio": ratio_val,
                "duration": dur_val
            }
            
            if ref_mode == "0. 纯文生视频 (支持联网)" and enable_web_search:
                payload["tools"] = [{"type": "web_search"}]
            
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
                while retry_count < 150: 
                    time.sleep(4) 
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
                            err_info = status_res_json.get("error")
                            if err_info and isinstance(err_info, dict):
                                err_msg = err_info.get("message", "未知原因")
                                err_code = err_info.get("code", "未知错误码")
                                log_api_error(f"❌ 引擎渲染失败 (状态: {current_status})\n\n原因: {err_msg} (错误码: {err_code})")
                            else:
                                log_api_error(f"❌ 引擎渲染失败 (状态: {current_status})\n\nAPI 未返回具体错误信息。")
                            break
                            
                    except Exception as poll_e:
                        log_api_error(f"⚠️ 轮询过程出现网络波动，系统正在自动重试: {poll_e}")
                        
            except Exception as e:
                log_api_error(f"网络通信出现严重故障，请稍后再试：{e}")
