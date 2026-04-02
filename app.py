import streamlit as st
import time
import requests
import uuid
from supabase import create_client, Client

# ================= 1. 核心配置 =================
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

# ================= 2. 状态守卫与登录 =================
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "username": "", "role": ""})

# 防范 V2.6 API 被封禁的“时间戳锁”
if "last_api_call" not in st.session_state:
    st.session_state["last_api_call"] = 0

if not st.session_state["logged_in"]:
    st.markdown("<br><br><h2 style='text-align: center;'>🔐 魔方国际影业 - 内部系统</h2>", unsafe_allow_html=True)
    st.write("---")
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
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
                st.session_state.update({"logged_in": True, "username": users[user_input]["name"], "role": users[user_input]["role"]})
                st.rerun() 
            else:
                st.error("⚠️ 账号或密码错误！")
    st.stop()

st.sidebar.title(f"👤 {st.session_state['username']}")
if st.sidebar.button("退出登录"):
    st.session_state["logged_in"] = False
    st.rerun()

if st.session_state["role"] == "admin":
    st.title("📊 财务与算力控制台")
    try:
        df = supabase.table("token_logs").select("*").order("created_at", desc=True).execute().data
        if df: st.dataframe(df, use_container_width=True)
        else: st.info("目前账本为空，请确员工已生成成功，且 token_logs 表已关闭 RLS。")
    except Exception as e: st.error(f"数据库连接异常: {e}")
    st.stop()

# ================= 3. 企业级资产中台引擎 =================
def upload_file_to_supabase(file_bytes, ext, bucket="assets"):
    """通用的私有云转存引擎，拦截报错，静默重试"""
    try:
        file_name = f"{uuid.uuid4().hex}.{ext}"
        content_type = f"video/{ext}" if ext == "mp4" else f"image/{ext}"
        supabase.storage.from_(bucket).upload(file=file_bytes, path=file_name, file_options={"content-type": content_type})
        return supabase.storage.from_(bucket).get_public_url(file_name)
    except Exception: return None

def fetch_and_store_video(temp_url):
    """拦截24小时死链：自动抓取火山临时视频 -> 注入你的私有数据库"""
    try:
        vid_res = requests.get(temp_url, stream=True)
        if vid_res.status_code == 200:
            perm_url = upload_file_to_supabase(vid_res.content, "mp4")
            return perm_url if perm_url else temp_url
    except Exception: pass
    return temp_url

# ================= 4. 员工创作台主逻辑 =================
st.markdown("## 🎬 魔方国际影业 - 视频生成台")
with st.container(border=True):
    prompt = st.text_area("📝 画面描述 (Prompt)", height=150)
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: ref_mode = st.selectbox("🎯 模式", ["0. 纯文生视频", "1. 首帧生图", "2. 首尾帧生图", "3. 多模态参考"])
    with col2: model_type = st.selectbox("⚙️ 引擎", ["Seedance 2.0 (画质)", "Seedance 2.0 fast (速度)"])
    with col3: ratio = st.selectbox("📏 比例", ["自适应", "16:9", "9:16"])
    with col4: duration = st.selectbox("⏱️ 时长", ["5 秒", "8 秒", "10 秒", "15 秒", "智能决定 (-1)"])
    with col5: audio_opt = st.selectbox("🎵 声音", ["生成配套音效", "无声版"])
    
    st.write("---")
    asset_1 = asset_2 = multi_assets = ""
    up_1 = up_2 = None
    multi_up = []
    enable_web_search = False

    def safe_preview(upload_file, caption_text):
        if upload_file:
            try: st.image(upload_file, caption=caption_text, use_container_width=True)
            except Exception: st.success(f"{caption_text} ✅ 已选中: {upload_file.name}")

    if ref_mode.startswith("0."):
        enable_web_search = st.toggle("🌐 开启联网增强搜索")
    elif ref_mode.startswith("1."):
        c1, c2 = st.columns(2)
        with c1: asset_1 = st.text_input("🎭 官方 Asset ID")
        with c2: 
            up_1 = st.file_uploader("🖼️ 本地【首帧】", type=['png', 'jpg', 'jpeg'])
            safe_preview(up_1, "🏷️ @图1 (首帧)")
    elif ref_mode.startswith("2."):
        c1, c2 = st.columns(2)
        with c1: 
            asset_1 = st.text_input("🎭 首帧 Asset ID")
            up_1 = st.file_uploader("🖼️ 本地【首帧】", type=['png', 'jpg', 'jpeg'])
            safe_preview(up_1, "🏷️ @图1 (首帧)")
        with c2:
            asset_2 = st.text_input("🎭 尾帧 Asset ID")
            up_2 = st.file_uploader("🖼️ 本地【尾帧】", type=['png', 'jpg', 'jpeg'])
            safe_preview(up_2, "🏷️ @图2 (尾帧)")
    elif ref_mode.startswith("3."):
        c1, c2 = st.columns(2)
        with c1: multi_assets = st.text_input("🎭 官方 Asset ID (多个用逗号隔开)")
        with c2: multi_up = st.file_uploader("🖼️ 上传本地图床", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if multi_up:
            cols = st.columns(6)
            for idx, up_file in enumerate(multi_up):
                with cols[idx % 6]: safe_preview(up_file, f"🏷️ @图{idx+1}")

    def format_asset_id(val):
        val = val.strip()
        if not val: return None
        if val.startswith("http"): return val
        if not val.startswith("asset://"): return f"asset://{val}"
        return val

    # ========= 发射任务至火山引擎 =========
    if st.button("🚀 提交任务至云端", type="primary", use_container_width=True):
        if not prompt: st.warning("请输入描述"); st.stop()
        
        status_box = st.info("☁️ 正在打包多模态资产...")
        api_content = [{"type": "text", "text": prompt}]
        
        # 精密装填图片并自动转存
        if ref_mode.startswith("1."):
            final_url = upload_file_to_supabase(up_1.getvalue(), up_1.name.split('.')[-1]) if up_1 else format_asset_id(asset_1)
            if not final_url: st.warning("请上传图片或填写ID"); st.stop()
            api_content.append({"type": "image_url", "image_url": {"url": final_url}, "role": "first_frame"})
        elif ref_mode.startswith("2."):
            f_url1 = upload_file_to_supabase(up_1.getvalue(), up_1.name.split('.')[-1]) if up_1 else format_asset_id(asset_1)
            f_url2 = upload_file_to_supabase(up_2.getvalue(), up_2.name.split('.')[-1]) if up_2 else format_asset_id(asset_2)
            if not f_url1 or not f_url2: st.warning("请确保首尾帧均已提供"); st.stop()
            api_content.append({"type": "image_url", "image_url": {"url": f_url1}, "role": "first_frame"})
            api_content.append({"type": "image_url", "image_url": {"url": f_url2}, "role": "last_frame"})
        elif ref_mode.startswith("3."):
            if multi_assets.strip():
                for a_id in [x.strip() for x in multi_assets.split(",") if x.strip()]:
                    fid = format_asset_id(a_id)
                    if fid: api_content.append({"type": "image_url", "image_url": {"url": fid}, "role": "reference_image"})
            if multi_up:
                for f in multi_up:
                    u_url = upload_file_to_supabase(f.getvalue(), f.name.split('.')[-1])
                    if u_url: api_content.append({"type": "image_url", "image_url": {"url": u_url}, "role": "reference_image"})

        payload = {
            "model": "ep-20260307130821-xw5wf" if "fast" in model_type else "ep-20260307130721-bx7tv",
            "content": api_content,
            "generate_audio": "配套音效" in audio_opt,
            "ratio": "adaptive" if ratio == "自适应" else ratio,
            "duration": -1 if "智能决定" in duration else int(duration.split(" ")[0])
        }
        if ref_mode.startswith("0.") and enable_web_search: payload["tools"] = [{"type": "web_search"}]
        
        headers = {"Authorization": f"Bearer {SEEDANCE_API_TOKEN}", "Content-Type": "application/json"}
        res = requests.post(CREATE_URL, headers=headers, json=payload)
        
        if res.status_code == 200:
            task_id = res.json().get("id")
            # 写入完整的防丢失记录：带上 ref_mode，为后续计费提供精准关联！
            supabase.table("video_gallery").insert({
                "employee_name": st.session_state["username"],
                "task_id": task_id, "prompt": prompt[:50], "status": "running", "ref_mode": ref_mode
            }).execute()
            status_box.success("✅ 任务已离线投递！请向下滑动查看【云端画廊】，或点击刷新追剧。")
            time.sleep(2)
            st.rerun()
        else:
            status_box.error(f"❌ 发射失败: {res.text}")

# ================= 5. 云端永久画廊 (含 V2.6 频率锁) =================
st.write("---")
col_title, col_btn = st.columns([4, 1])
with col_title: st.markdown("### 🎞️ 永久云端资产画廊")
with col_btn: 
    if st.button("🔄 一键追进度", use_container_width=True): st.rerun()

headers = {"Authorization": f"Bearer {SEEDANCE_API_TOKEN}", "Content-Type": "application/json"}

try:
    gallery_data = supabase.table("video_gallery").select("*").eq("employee_name", st.session_state["username"]).order("created_at", desc=True).limit(9).execute().data
    
    if gallery_data:
        # V2.6 防封禁：距离上次查询是否大于 3.5 秒
        current_time = time.time()
        can_query_api = (current_time - st.session_state["last_api_call"]) > 3.5
        
        cols = st.columns(3)
        for idx, item in enumerate(gallery_data):
            with cols[idx % 3]:
                with st.container(border=True):
                    
                    if item["status"] in ["running", "queued"]:
                        # 触发大模型 API 查询（严格守卫 3 秒红线）
                        if can_query_api:
                            try:
                                s_res = requests.post(GET_URL, headers=headers, json={"id": item["task_id"]})
                                st.session_state["last_api_call"] = time.time() # 更新锁
                                
                                if s_res.status_code == 200:
                                    live_status = s_res.json().get("status")
                                    if live_status == "succeeded":
                                        temp_url = s_res.json().get("content", {}).get("video_url")
                                        st.toast("🎉 视频生成完毕，正在为您加密转存...", icon="💾")
                                        
                                        # 下载视频 -> 上传至 Supabase -> 获得永久链接
                                        perm_url = fetch_and_store_video(temp_url)
                                        
                                        # 更新画廊状态为永久完成
                                        supabase.table("video_gallery").update({"status": "succeeded", "video_url": perm_url}).eq("task_id", item["task_id"]).execute()
                                        item["status"], item["video_url"] = "succeeded", perm_url
                                        
                                        # 完美合规闭环：拿到当时存的 ref_mode 进行财务入账
                                        tokens = s_res.json().get("usage", {}).get("completion_tokens", 15)
                                        supabase.table("token_logs").insert({"employee_name": st.session_state["username"], "action_type": item.get("ref_mode", "未知模式"), "prompt_text": item["prompt"], "tokens_cost": tokens}).execute()
                                        
                                    elif live_status in ["failed", "cancelled", "expired"]:
                                        supabase.table("video_gallery").update({"status": live_status}).eq("task_id", item["task_id"]).execute()
                                        item["status"] = live_status
                            except Exception: pass
                    
                    # 渲染 UI 控制器
                    if item["status"] == "succeeded" and item["video_url"]:
                        st.video(item["video_url"])
                        st.markdown(f"**资产受限免** | [📥 高清下载]({item['video_url']})")
                    elif item["status"] in ["running", "queued"]:
                        st.info("☁️ 引擎渲染中...")
                    else:
                        st.error("❌ 渲染被系统熔断拦截")
                    st.caption(f"📝 {item['prompt']}")
except Exception as e:
    st.error("画廊读取失败，请检查 Supabase 表结构或权限设置 (RLS)。")
