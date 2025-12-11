import streamlit as st
import zipfile
import os
import base64
import json
import glob
import time  # ←エラー修正：ここ（一番上）に移動しました！
import streamlit.components.v1 as components

# ==========================================
# ページ設定
# ==========================================
st.set_page_config(page_title="My Menu Book", layout="centered")

st.markdown("""
<style>
    /* 全体のフォント調整 */
    body { font-family: sans-serif; }
    /* タイトルの装飾 */
    h1 { color: #ff4b4b; }
</style>
""", unsafe_allow_html=True)

st.title("🎧 My Menu Book")

# ==========================================
# 1. データ管理システム（フォルダ保存）
# ==========================================
# 本棚のデータを保存するフォルダを作成
LIBRARY_DIR = "library"
if not os.path.exists(LIBRARY_DIR):
    os.makedirs(LIBRARY_DIR)

# --- サイドバー：管理者メニュー（お店の追加・削除） ---
with st.sidebar:
    st.header("🔧 管理者メニュー")
    
    # ファイルアップロード
    uploaded_zips = st.file_uploader(
        "新しいお店のメニュー(ZIP)を追加", 
        type="zip", 
        accept_multiple_files=True
    )
    
    if uploaded_zips:
        count = 0
        for zfile in uploaded_zips:
            # libraryフォルダに保存
            save_path = os.path.join(LIBRARY_DIR, zfile.name)
            with open(save_path, "wb") as f:
                f.write(zfile.getbuffer())
            count += 1
        
        st.success(f"{count}店舗を追加しました！")
        
        # 画面を更新してリストに反映
        time.sleep(1) 
        st.rerun()

    st.divider()
    
    # データの削除機能
    st.subheader("🗑️ お店の整理")
    # 大文字小文字に関わらずzipファイルを探す
    files = os.listdir(LIBRARY_DIR)
    existing_files = [f for f in files if f.lower().endswith('.zip')]
    
    if existing_files:
        files_to_delete = st.multiselect(
            "削除するお店を選択",
            existing_files
        )
        if files_to_delete and st.button("選択したお店を削除"):
            for f in files_to_delete:
                os.remove(os.path.join(LIBRARY_DIR, f))
            st.success("削除しました")
            time.sleep(1)
            st.rerun()

# フォルダから現在のお店リストを作成
bookshelf = {}
# 再度ファイルを取得してリスト化
files = os.listdir(LIBRARY_DIR)
for filename in files:
    if filename.lower().endswith('.zip'):
        file_path = os.path.join(LIBRARY_DIR, filename)
        # 拡張子(.zip)を取り除いて店名にする
        store_name = os.path.splitext(filename)[0]
        # ファイル名のアンダースコアをスペースに戻して綺麗に表示
        display_name = store_name.replace("_", " ")
        bookshelf[display_name] = file_path

# ==========================================
# 2. セッション状態
# ==========================================
if 'selected_shop' not in st.session_state:
    st.session_state.selected_shop = None

# ==========================================
# 3. プレイヤー生成関数（安全なHTML生成版）
# ==========================================
def render_custom_player(shop_name):
    zip_path = bookshelf[shop_name]
    
    # 1. ZIPから全トラックをBase64化
    playlist_data = []
    
    with zipfile.ZipFile(zip_path) as z:
        # ファイル名で並び替え（数字順になるように）
        file_list = sorted(z.namelist())
        for f in file_list:
            if f.endswith(".mp3"):
                data = z.read(f)
                b64_data = base64.b64encode(data).decode()
                # タイトルの整形（"01_前菜.mp3" -> "01 前菜"）
                title = f.replace(".mp3", "").replace("_", " ")
                
                playlist_data.append({
                    "title": title,
                    "src": f"data:audio/mp3;base64,{b64_data}"
                })
    
    playlist_json = json.dumps(playlist_data, ensure_ascii=False)

    # 2. HTMLテンプレート
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        .player-container { border: 2px solid #e0e0e0; border-radius: 15px; padding: 20px; background-color: #f9f9f9; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .track-title { font-size: 20px; font-weight: bold; color: #333; margin-bottom: 15px; min-height: 1.5em; padding: 10px; background: #fff; border-radius: 8px; border-left: 5px solid #ff4b4b; }
        .controls { display: flex; justify-content: space-between; align-items: center; margin: 15px 0; gap: 10px; }
        button { flex: 1; padding: 15px 10px; font-size: 18px; font-weight: bold; color: white; background-color: #ff4b4b; border: none; border-radius: 8px; cursor: pointer; }
        button:active { opacity: 0.7; }
        .speed-control { margin-top: 15px; font-size: 14px; color: #666; }
        audio { width: 100%; height: 40px; margin-top: 10px; }
        .track-list { margin-top: 20px; text-align: left; max-height: 250px; overflow-y: auto; border-top: 1px solid #ddd; padding-top: 10px; }
        .track-item { padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; font-size: 16px; }
        .track-item.active { background-color: #ffecec; font-weight: bold; color: #ff4b4b; }
    </style>
    </head>
    <body>

    <div class="player-container">
        <div class="track-title" id="current-title">Loading...</div>
        <audio id="audio-player" controls></audio>
        <div class="controls">
            <button onclick="prevTrack()">⏮ 前へ</button>
            <button onclick="togglePlay()" id="play-btn">▶ 再生</button>
            <button onclick="nextTrack()">次へ ⏭</button>
        </div>
        <div class="speed-control">
            速度: 
            <select id="speed-select" onchange="changeSpeed()">
                <option value="1.0">1.0x</option>
                <option value="1.2">1.2x</option>
                <option value="1.4" selected>1.4x (推奨)</option>
                <option value="2.0">2.0x</option>
            </select>
        </div>
        <div class="track-list" id="playlist-container"></div>
    </div>

    <script>
        const playlist = __PLAYLIST_JSON__;
        let currentIdx = 0;
        const audio = document.getElementById('audio-player');
        const titleEl = document.getElementById('current-title');
        const playBtn = document.getElementById('play-btn');
        const listContainer = document.getElementById('playlist-container');

        function init() { renderPlaylist(); loadTrack(0); changeSpeed(); }
        
        function loadTrack(index) {
            if (index < 0 || index >= playlist.length) return;
            currentIdx = index;
            audio.src = playlist[currentIdx].src;
            titleEl.textContent = playlist[currentIdx].title;
            updateListHighlight();
        }

        function togglePlay() {
            if (audio.paused) {
                audio.play().then(() => { playBtn.textContent = "⏸ 停止"; }).catch(e => console.error(e));
            } else {
                audio.pause();
                playBtn.textContent = "▶ 再生";
            }
        }

        function nextTrack() {
            if (currentIdx < playlist.length - 1) { loadTrack(currentIdx + 1); audio.play(); playBtn.textContent = "⏸ 停止"; }
        }

        function prevTrack() {
            if (currentIdx > 0) { loadTrack(currentIdx - 1); audio.play(); playBtn.textContent = "⏸ 停止"; }
        }

        function changeSpeed() {
            const speed = document.getElementById('speed-select').value;
            audio.playbackRate = parseFloat(speed);
        }

        audio.onended = function() {
            if (currentIdx < playlist.length - 1) { nextTrack(); } 
            else { playBtn.textContent = "▶ 再生"; }
        };

        audio.onplay = function() { changeSpeed(); playBtn.textContent = "⏸ 停止"; };
        audio.onpause = function() { playBtn.textContent = "▶ 再生"; };

        function renderPlaylist() {
            listContainer.innerHTML = "";
            playlist.forEach((track, idx) => {
                const div = document.createElement('div');
                div.className = "track-item";
                div.textContent = (idx + 1) + ". " + track.title;
                div.onclick = () => { loadTrack(idx); audio.play(); };
                div.id = "track-" + idx;
                listContainer.appendChild(div);
            });
        }

        function updateListHighlight() {
            const items = document.querySelectorAll('.track-item');
            items.forEach(item => item.classList.remove('active'));
            const activeItem = document.getElementById("track-" + currentIdx);
            if (activeItem) {
                activeItem.classList.add('active');
                activeItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        }

        init();
    </script>
    </body>
    </html>
    """
    
    # Python変数をJSに埋め込む
    final_html = html_template.replace("__PLAYLIST_JSON__", playlist_json)
    
    st.components.v1.html(final_html, height=600)

# =
