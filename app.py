import streamlit as st
import zipfile
import os
import io

# ==========================================
# 修正箇所：layoutを "mobile" から "centered" に変更しました
# ==========================================
st.set_page_config(page_title="Menu Bookshelf", layout="centered")

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
# 2. 検索機能（音声入力対応）
# ==========================================
st.markdown("### 🔍 お店を探す")
st.info("下の入力欄をタップして、キーボードのマイクボタンで話しかけてください。")

search_query = st.text_input("お店の名前を入力（音声検索対応）", placeholder="例：カフェ")

filtered_shops = []
if search_query:
    for name in bookshelf.keys():
        if search_query in name:
            filtered_shops.append(name)
else:
    filtered_shops = list(bookshelf.keys())

# ==========================================
# 3. お店リスト（本棚）の表示
# ==========================================
st.markdown("---")
st.subheader(f"📚 お店リスト ({len(filtered_shops)}件)")

if 'selected_shop' not in st.session_state:
    st.session_state.selected_shop = None

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
    
    if st.button("❌ 閉じてリストに戻る"):
        st.session_state.selected_shop = None
        st.rerun()

    try:
        with zipfile.ZipFile(target_zip) as z:
            file_list = sorted(z.namelist())
            
            for file_name in file_list:
                if file_name.endswith(".mp3"):
                    audio_data = z.read(file_name)
                    track_title = file_name.replace(".mp3", "").replace("_", " ")
                    
                    st.write(f"**{track_title}**")
                    st.audio(audio_data, format="audio/mp3")
                    
    except Exception as e:
        st.error(f"再生エラー: {e}")

elif len(filtered_shops) == 0 and uploaded_zips:
    st.warning("該当するお店が見つかりませんでした。")
    
elif not uploaded_zips:
    st.write("👆 まずは上の「管理者メニュー」からZIPファイルを追加してください。")
