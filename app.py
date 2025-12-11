import streamlit as st
import zipfile
import os
import io
import base64

# ==========================================
# ページ設定
# ==========================================
st.set_page_config(page_title="Menu Bookshelf", layout="centered")

st.markdown("""
<style>
    /* ボタンを大きく押しやすく */
    .stButton > button {
        width: 100%;
        height: 3.5em;
        font-size: 20px !important;
        font-weight: bold;
        margin-bottom: 10px;
        border-radius: 10px;
    }
    /* 再生中のタイトル装飾 */
    .playing-title {
        font-size: 24px;
        font-weight: bold;
        color: #e63946;
        padding: 10px;
        border: 2px solid #e63946;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        background-color: #fff5f5;
    }
    audio {
        width: 100%;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎧 メニュー本棚")

# ==========================================
# 1. データ準備・設定
# ==========================================
with st.expander("管理者メニュー：ZIPファイルの追加"):
    uploaded_zips = st.file_uploader(
        "作成したZIPファイルをここに登録", 
        type="zip", 
        accept_multiple_files=True
    )

st.sidebar.header("🔊 設定")
playback_speed = st.sidebar.slider("再生速度", 0.5, 2.0, 1.4, 0.1)

bookshelf = {}
if uploaded_zips:
    for zfile in uploaded_zips:
        store_name = os.path.splitext(zfile.name)[0]
        display_name = store_name.replace("_", " ")
        bookshelf[display_name] = zfile

# ==========================================
# 2. セッション状態
# ==========================================
if 'selected_shop' not in st.session_state:
    st.session_state.selected_shop = None
if 'current_track_idx' not in st.session_state:
    st.session_state.current_track_idx = 0
if 'playlist' not in st.session_state:
    st.session_state.playlist = [] 
# 自動再生の状態管理（Trueなら再生、Falseなら停止）
if 'is_playing' not in st.session_state:
    st.session_state.is_playing = True

# ==========================================
# 3. ロジック関数
# ==========================================
def load_playlist(shop_name):
    zip_file = bookshelf[shop_name]
    new_playlist = []
    with zipfile.ZipFile(zip_file) as z:
        file_list = sorted(z.namelist())
        for f in file_list:
            if f.endswith(".mp3"):
                data = z.read(f)
                title = f.replace(".mp3", "").replace("_", " ")
                new_playlist.append({"title": title, "data": data})
    st.session_state.playlist = new_playlist
    st.session_state.current_track_idx = 0
    st.session_state.selected_shop = shop_name
    st.session_state.is_playing = True # 読み込んだらすぐ再生

def next_track():
    if st.session_state.current_track_idx < len(st.session_state.playlist) - 1:
        st.session_state.current_track_idx += 1
        st.session_state.is_playing = True # 次へ行ったら再生

def prev_track():
    if st.session_state.current_track_idx > 0:
        st.session_state.current_track_idx -= 1
        st.session_state.is_playing = True # 戻ったら再生

def toggle_play():
    """再生/停止を切り替え"""
    st.session_state.is_playing = not st.session_state.is_playing

def close_player():
    st.session_state.selected_shop = None
    st.session_state.playlist = []
    st.session_state.current_track_idx = 0
    st.session_state.is_playing = True

# カスタムプレイヤー（autoplayを制御できるように改造）
def play_audio_custom(audio_bytes, speed, auto_play):
    b64 = base64.b64encode(audio_bytes).decode()
    
    # auto_playがTrueなら 'autoplay' 属性をつける
    autoplay_attr = "autoplay" if auto_play else ""
    
    html_code = f"""
    <audio id="custom_player" controls {autoplay_attr}>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    <script>
        var audio = document.getElementById("custom_player");
        audio.playbackRate = {speed};
    </script>
    """
    st.markdown(html_code, unsafe_allow_html=True)

# ==========================================
# 4. 画面表示
# ==========================================
if st.session_state.selected_shop:
    shop_name = st.session_state.selected_shop
    playlist = st.session_state.playlist
    current_idx = st.session_state.current_track_idx
    
    if not playlist:
        st.error("データなし")
        if st.button("戻る"):
            close_player()
            st.rerun()
        st.stop()

    current_track = playlist[current_idx]

    st.caption(f"再生中: {shop_name}")
    
    # --- コントローラー（3列に分割） ---
    col_prev, col_pause, col_next = st.columns([1, 1, 1])
    
    with col_prev:
        if st.button("⏮ 前へ", disabled=(current_idx == 0), use_container_width=True):
            prev_track()
            st.rerun()
            
    with col_pause:
        # 再生中なら「停止ボタン」、停止中なら「再生ボタン」を表示
        if st.session_state.is_playing:
            label = "⏸ 停止"
        else:
            label = "▶ 再生"
            
        if st.button(label, use_container_width=True):
            toggle_play()
            st.rerun()

    with col_next:
        if st.button("次へ ⏭", disabled=(current_idx == len(playlist)-1), use_container_width=True):
            next_track()
            st.rerun()

    # タイトル
    st.markdown(f'<div class="playing-title">{current_track["title"]}</div>', unsafe_allow_html=True)
    
    # プレイヤー（is_playingの状態を渡す）
    play_audio_custom(current_track["data"], playback_speed, st.session_state.is_playing)

    st.write(f"Track {current_idx + 1} / {len(playlist)}")
    
    with st.expander("トラックリスト"):
        for i, track in enumerate(playlist):
            label = f"♪ {track['title']}"
            if i == current_idx:
                label = f"🔴 {label}"
            if st.button(label, key=f"jump_{i}"):
                st.session_state.current_track_idx = i
                st.session_state.is_playing = True
                st.rerun()

    st.divider()
    if st.button("❌ 閉じる"):
        close_player()
        st.rerun()

else:
    # リスト画面
    st.markdown("### 🔍 お店を探す")
    st.info("下の入力欄をタップして、キーボードのマイクボタンで話しかけてください。")
    search_query = st.text_input("お店の名前を入力", placeholder="例：カフェ")

    filtered_shops = []
    if search_query:
        for name in bookshelf.keys():
            if search_query in name:
                filtered_shops.append(name)
    else:
        filtered_shops = list(bookshelf.keys())

    st.markdown("---")
    st.subheader(f"📚 お店リスト ({len(filtered_shops)}件)")

    if not uploaded_zips:
        st.warning("👆 管理者メニューからZIPを追加してください。")

    for shop_name in filtered_shops:
        if st.button(f"▶ {shop_name} を聴く"):
            load_playlist(shop_name)
            st.rerun()
