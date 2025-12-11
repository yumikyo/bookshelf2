import streamlit as st
import zipfile
import os
import io

# ページ設定
st.set_page_config(page_title="Menu Bookshelf", layout="mobile")

# CSSでボタンを押しやすく大きくする（アクセシビリティ対応）
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        height: 3em;
        font-size: 20px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    /* 検索ボックスの文字を大きく */
    .stTextInput > div > div > input {
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎧 メニュー本棚")

# ==========================================
# 1. データの準備（ZIPアップロード）
# ==========================================
# 本来はサーバーにあるデータを読み込みますが、
# ここではデモとして「作ったZIP」をアップロードして本棚に入れます。
with st.expander("管理者メニュー：ZIPファイルの追加"):
    uploaded_zips = st.file_uploader(
        "作成したZIPファイルをここに登録", 
        type="zip", 
        accept_multiple_files=True
    )

# アップロードされたファイルを辞書形式で保持
# キー: 店名（ファイル名から抽出）, 値: ZIPデータ
bookshelf = {}

if uploaded_zips:
    for zfile in uploaded_zips:
        # ファイル名から「.zip」を除去して店名とする
        # 例: "カフェタナカ_20251211.zip" -> "カフェタナカ_20251211"
        store_name = os.path.splitext(zfile.name)[0]
        # 見やすいようにアンダースコアをスペースに（読み上げ用）
        display_name = store_name.replace("_", " ")
        bookshelf[display_name] = zfile

# ==========================================
# 2. 検索機能（音声入力対応）
# ==========================================
st.markdown("### 🔍 お店を探す")
st.info("下の入力欄をタップして、キーボードのマイクボタンで話しかけてください。")

# 検索ボックス（ここがボイスリサーチの入口になります）
search_query = st.text_input("お店の名前を入力（音声検索対応）", placeholder="例：カフェ")

# 検索フィルター処理
filtered_shops = []
if search_query:
    # 検索ワードが含まれるお店だけをピックアップ
    for name in bookshelf.keys():
        if search_query in name:
            filtered_shops.append(name)
else:
    # 検索していない時は全店表示
    filtered_shops = list(bookshelf.keys())

# ==========================================
# 3. お店リスト（本棚）の表示
# ==========================================
st.markdown("---")
st.subheader(f"📚 お店リスト ({len(filtered_shops)}件)")

# 選択されたお店を保存するセッション状態
if 'selected_shop' not in st.session_state:
    st.session_state.selected_shop = None

# お店ボタンの生成
for shop_name in filtered_shops:
    if st.button(f"▶ {shop_name} を開く"):
        st.session_state.selected_shop = shop_name

# ==========================================
# 4. 再生画面
# ==========================================
if st.session_state.selected_shop and st.session_state.selected_shop in bookshelf:
    target_shop = st.session_state.selected_shop
    target_zip = bookshelf[target_shop]
    
    st.markdown("---")
    st.markdown(f"## 💿 再生中: {target_shop}")
    
    # 閉じるボタン
    if st.button("❌ 閉じてリストに戻る"):
        st.session_state.selected_shop = None
        st.rerun()

    # ZIPの中身を展開して再生プレイヤーを表示
    try:
        with zipfile.ZipFile(target_zip) as z:
            # ファイルリストを取得し、名前順（01, 02...）にソート
            file_list = sorted(z.namelist())
            
            for file_name in file_list:
                if file_name.endswith(".mp3"):
                    # ZIP内の音声データをメモリ上で読み込む
                    audio_data = z.read(file_name)
                    
                    # ファイル名からトラック情報をきれいに表示
                    # 例: "01_はじめに・目次.mp3" -> "01 はじめに・目次"
                    track_title = file_name.replace(".mp3", "").replace("_", " ")
                    
                    st.write(f"**{track_title}**")
                    st.audio(audio_data, format="audio/mp3")
                    
    except Exception as e:
        st.error
