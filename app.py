import streamlit as st
import zipfile
import os
import base64
import json

# ==========================================
# ページ設定
# ==========================================
st.set_page_config(page_title="Menu Bookshelf", layout="centered")

st.markdown("""
<style>
    /* 全体のフォント調整 */
    body {
        font-family: sans-serif;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎧 メニュー本棚")

# ==========================================
# 1. データ準備（ZIP管理）
# ==========================================
with st.expander("管理者メニュー：ZIPファイルの追加"):
    uploaded_zips = st.file_uploader(
        "作成したZIPファイルをここに登録", 
        type="zip", 
        accept_multiple_files=True
    )

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

# ==========================================
# 3. プレイヤー生成関数（HTML/JS埋め込み）
# ==========================================
def render_custom_player(shop_name):
    zip_file = bookshelf[shop_name]
    
    # 1. 全トラックのデータをBase64化してリストにする
    # ※データ量が多いと少しロードに時間がかかりますが、動作は最もスムーズです
    playlist_data = []
    
    with zipfile.ZipFile(zip_file) as z:
        file_list = sorted(z.namelist())
        for f in file_list:
            if f.endswith(".mp3"):
                data = z.read(f)
                b64_data = base64.b64encode(data).decode()
                title = f.replace(".mp3", "").replace("_", " ")
                # JSに渡すための辞書リスト
                playlist_data.append({
                    "title": title,
                    "src": f"data:audio/mp3;base64,{b64_data}"
                })
    
    # PythonのリストをJSON文字列（JSの配列）に変換
    playlist_json = json.dumps(playlist_data)

    # 2. カスタムプレイヤーのHTML/CSS/JSを構築
    # ここに「普通のプレイヤー」の全ロジック（連続再生など）を詰め込みます
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        /* プレイヤーのデザイン */
        .player-container {{
            border: 2px solid #e0e0e0;
            border-radius: 15px;
            padding: 20px;
            background-color: #f9f9f9;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .track-title {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            min-height: 1.5em;
            padding: 10px;
            background: #fff;
            border-radius: 8px;
            border-left: 5px solid #ff4b4b;
        }}
        .controls {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 15px 0;
            gap: 10px;
        }}
        button {{
            flex: 1;
            padding: 15px 10px;
            font-size: 18px;
            font-weight: bold;
            color: white;
            background-color: #ff4b4b;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        button:active {{
            opacity: 0.7;
        }}
        button:disabled {{
            background-color: #ccc;
            cursor: not-allowed;
        }}
        .speed-control {{
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }}
        audio {{
            width: 100%;
            height: 40px;
            margin-top: 10px;
        }}
        .track-list {{
            margin-top: 20px;
            text-align: left;
            max-height: 200px;
            overflow-y: auto;
            border-top: 1px solid #ddd;
            padding-top: 10px;
        }}
        .track-item {{
            padding: 8px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            font-size: 14px;
        }}
        .track-item.active {{
            background-color: #ffecec;
            font-weight: bold;
            color: #ff4b4b;
        }}
    </style>
    </head>
    <body>

    <div class="player-container">
        <div class="track-title" id="current-title">読み込み中...</div>

        <audio id="audio-player" controls></audio>

        <div class="controls">
            <button onclick="prevTrack()">⏮ 前へ</button>
            <button onclick="togglePlay()" id="play-btn">▶ 再生</button>
            <button onclick="nextTrack()">次へ ⏭</button>
        </div>

        <div class="speed-control">
            再生速度: 
            <select id="speed-select" onchange="changeSpeed()">
                <option value="1.0">標準 (1.0x)</option>
                <option value="1.2">少し速く (1.2x)</option>
                <option value="1.4" selected>サクサク (1.4x)</option>
                <option value="2.0">爆速 (2.0x)</option>
            </select>
        </div>

        <div class="track-list" id="playlist-container"></div>
    </div>

    <script>
        // Pythonから受け取ったプレイリストデータ
        const playlist = {playlist_json};
        let currentIdx = 0;
        const audio = document.getElementById('audio-player');
        const titleEl = document.getElementById('current-title');
        const playBtn = document.getElementById('play-btn');
        const listContainer = document.getElementById('playlist-container');

        // 初期設定
        function init() {{
            renderPlaylist();
            loadTrack(0);
            changeSpeed(); // 初期の速度設定を適用
        }}

        // トラックの読み込み
        function loadTrack(index) {{
            if (index < 0 || index >= playlist.length) return;
            currentIdx = index;
            
            // 音源セット
            audio.src = playlist[currentIdx].src;
            titleEl.textContent = playlist[currentIdx].title;
            
            // リストのハイライト更新
            updateListHighlight();
            
            // 再生状態のリセットはしない（連続再生のため）
        }}

        // 再生・一時停止切り替え
        function togglePlay() {{
            if (audio.paused) {{
                audio.play()
                    .then(() => {{
                        playBtn.textContent = "⏸ 停止";
                    }})
                    .catch(e => console.error(e));
            }} else {{
                audio.pause();
                playBtn.textContent = "▶ 再生";
            }}
        }}

        // 次の曲へ（自動再生付き）
        function nextTrack() {{
            if (currentIdx < playlist.length - 1) {{
                loadTrack(currentIdx + 1);
                audio.play(); // 強制再生
                playBtn.textContent = "⏸ 停止";
            }}
        }}

        // 前の曲へ
        function prevTrack() {{
            if (currentIdx > 0) {{
                loadTrack(currentIdx - 1);
                audio.play();
                playBtn.textContent = "⏸ 停止";
            }}
        }}

        // 速度変更
        function changeSpeed() {{
            const speed = document.getElementById('speed-select').value;
            audio.playbackRate = parseFloat(speed);
        }}

        // ★重要：曲が終わったら自動で次へ
        audio.onended = function() {{
            if (currentIdx < playlist.length - 1) {{
                nextTrack();
            }} else {{
                // 最後の曲が終わったら停止状態に戻す
                playBtn.textContent = "▶ 再生";
            }}
        }};

        // 速度設定は再生が始まるたびにリセットされることがあるので監視
        audio.onplay = function() {{
            changeSpeed();
            playBtn.textContent = "⏸ 停止";
        }};
        
        audio.onpause = function() {{
            playBtn.textContent = "▶ 再生";
        }};

        // プレイリスト描画
        function renderPlaylist() {{
            listContainer.innerHTML = "";
            playlist.forEach((track, idx) => {{
                const div = document.createElement('div');
                div.className = "track-item";
                div.textContent = (idx + 1) + ". " + track.title;
                div.onclick = () => {{
                    loadTrack(idx);
                    audio.play();
                }};
                div.id = "track-" + idx;
                listContainer.appendChild(div);
            }});
        }}

        function updateListHighlight() {{
            // 全てのハイライトを消す
            const items = document.querySelectorAll('.track-item');
            items.forEach(item => item.classList.remove('active'));
            
            // 現在の曲をハイライト
            const activeItem = document.getElementById("track-" + currentIdx);
            if (activeItem) {{
                activeItem.classList.add('active');
                // スクロール位置調整
                activeItem.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
            }}
        }}

        // 開始
        init();

    </script>
    </body>
    </html>
    """
    
    # HTMLを埋め込む（高さは適当に確保）
    st.components.v1.html(html_code, height=600)


# ==========================================
# 4. 画面表示切り替え
# ==========================================
if st.session_state.selected_shop:
    shop_name = st.session_state.selected_shop
    
    st.caption(f"再生中: {shop_name}")
    
    # 閉じるボタン（これはStreamlit側の制御）
    if st.button("❌ 閉じてリストに戻る"):
        st.session_state.selected_shop = None
        st.rerun()
        
    st.markdown("---")
    
    # ★カスタムプレイヤーの表示★
    try:
        render_custom_player(shop_name)
    except Exception as e:
        st.error(f"プレイヤーの読み込みに失敗しました: {e}")

else:
    # --- リスト画面 ---
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
            st.session_state.selected_shop = shop_name
            st.rerun()
