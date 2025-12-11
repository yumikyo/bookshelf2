import streamlit as st
import zipfile
import os
import io

# ==========================================
# ページ設定（スマホで見やすく）
# ==========================================
st.set_page_config(page_title="Menu Bookshelf", layout="centered")

# CSSでボタンを大きくし、操作しやすくする
st.markdown("""
<style>
    /* ボタン全般を大きく */
    .stButton > button {
        width: 100%;
        height: 3.5em;
        font-size: 22px !important;
        font-weight: bold;
        margin-bottom: 10px;
        border-radius: 10px;
    }
    /* 再生中のタイトルを目立たせる */
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
</style>
""", unsafe_allow_html=True)

st.title("🎧 メニュー本棚")

# ==========================================
# 1. データの準備（ZIPアップロード）
# ==========================================
with st.expander("管理者メニュー：ZIPファイルの追加"):
    uploaded_zips = st.file_uploader(
        "作成したZIPファイルをここに登録", 
        type="zip", 
        accept_multiple_files=True
    )

# アップロードされたファイルを辞書形式で保持
bookshelf = {}
if uploaded_zips:
    for zfile in uploaded_zips:
        store_name = os.path.splitext(zfile.name)[0]
        display_name = store_name.replace("_", " ")
        bookshelf[display_name] = zfile

# ==========================================
# 2. セッション状態の管理
# ==========================================
# 選んだお店
if 'selected_shop' not in st.session_state:
    st.session_state.selected_shop = None
# 現在のトラック番号（0番始まり）
if 'current_track_idx' not in st.session_state:
    st.session_state.current_track_idx = 0
# 再生リスト（メモリ上に展開した音声データ）
if 'playlist' not in st.session_state:
    st.session_state.playlist = [] # [{"title": "...", "data": bytes}, ...]

# ==========================================
# 3. ロジック関数
# ==========================================
def load_playlist(shop_name):
    """ZIPを解凍してメモリ上のプレイリストを作る"""
    zip_file = bookshelf[shop_name]
    new_playlist = []
    
    with zipfile.ZipFile(zip_file) as z:
        # 名前順にソートして取り出す
        file_list = sorted(z.namelist())
        for f in file_list:
            if f.endswith(".mp3"):
                data = z.read(f)
                # タイトルをきれいにする
                title = f.replace(".mp3", "").replace("_", " ")
                new_playlist.append({"title": title, "data": data})
    
    st.session_state.playlist = new_playlist
    st.session_state.current_track_idx = 0
    st.session_state.selected_shop = shop_name

def next_track():
    """次の曲へ"""
    if st.session_state.current_track_idx < len(st.session_state.playlist) - 1:
        st.session_state.current_track_idx += 1

def prev_track():
    """前の曲へ"""
    if st.session_state.current_track_idx > 0:
        st.session_state.current_track_idx -= 1

def close_player():
    """プレイヤーを閉じる"""
    st.session_state.selected_shop = None
    st.session_state.playlist = []
    st.session_state.current_track_idx = 0

# ==========================================
# 4. 画面表示：プレイヤーモード or リストモード
# ==========================================

# --- A. プレイヤー画面（お店選択中） ---
if st.session_state.selected_shop:
    shop_name = st.session_state.selected_shop
    playlist = st.session_state.playlist
    current_idx = st.session_state.current_track_idx
    
    # 万が一プレイリストが空の場合のエラー回避
    if not playlist:
        st.error("音声データが見つかりませんでした。")
        if st.button("戻る"):
            close_player()
            st.rerun()
        st.stop()

    current_track = playlist[current_idx]

    # ヘッダー
    st.caption(f"再生中のお店: {shop_name}")
    
    # --- コントローラー（戻る・進む） ---
    col_prev, col_next = st.columns(2)
    
    with col_prev:
        # 最初の曲のときはボタンを押せなくする（disabled）
        if st.button("⏮ 前へ", disabled=(current_idx == 0), use_container_width=True):
            prev_track()
            st.rerun()
            
    with col_next:
        # 最後の曲のときはボタンを押せなくする
        if st.button("次へ ⏭", disabled=(current_idx == len(playlist)-1), use_container_width=True, type="primary"):
            next_track()
            st.rerun()

    # --- メイン再生エリア ---
    st.markdown(f'<div class="playing-title">{current_track["title"]}</div>', unsafe_allow_html=True)
    
    # 音声プレイヤー
    # autoplay=True にすることで、「次へ」を押した瞬間に再生が始まります
    st.audio(current_track["data"], format="audio/mp3", autoplay=True)

    # 現在位置の表示（例: 1 / 10）
    st.write(f"Track {current_idx + 1} / {len(playlist)}")
    
    # プレイリスト一覧（下部に表示して、直接ジャンプできるようにする）
    with st.expander("トラックリストを開く"):
        for i, track in enumerate(playlist):
            # 今再生中の曲は太字にする
            label = f"♪ {track['title']}"
            if i == current_idx:
                label = f"🔴 {label} (再生中)"
            
            if st.button(label, key=f"jump_{i}"):
                st.session_state.current_track_idx = i
                st.rerun()

    st.divider()
    if st.button("❌ お店リストに戻る"):
        close_player()
        st.rerun()

# --- B. お店リスト画面（未選択時） ---
else:
    # 検索機能
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
        st.warning("👆 まずは上の「管理者メニュー」からZIPファイルを追加してください。")
    elif len(filtered_shops) == 0:
        st.warning("見つかりませんでした。")

    for shop_name in filtered_shops:
        # ボタンを押すと、データをロードしてプレイヤー画面へ切り替わる
        if st.button(f"▶ {shop_name} を聴く"):
            load_playlist(shop_name)
            st.rerun()
