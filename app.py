import streamlit as st
import zipfile
import base64
import json
import os
import re
import streamlit.components.v1 as components

# ページ設定
st.set_page_config(page_title="My Menu Book", layout="centered")

# CSSによるアクセシビリティ強化（フォーカスリングの明示化など）
st.markdown("""
<style>
    body { font-family: sans-serif; }
    h1 { color: #ff4b4b; }
    
    /* ボタンの視認性向上 */
    .stButton button { 
        width: 100%; 
        font-weight: bold; 
        border-radius: 8px;
        min-height: 50px; /* タップ領域確保 */
    }
    
    /* キーボード操作時のフォーカスリングを強調 */
    .stButton button:focus {
        outline: 3px solid #333 !important;
        outline-offset: 2px !important;
    }
    
    /* 入力欄のフォーカスも見やすく */
    input:focus {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 0 2px rgba(255, 75, 75, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎧 My Menu Book")

# データ管理
if 'my_library' not in st.session_state:
    st.session_state.my_library = {}

# --- サイドバー：本の追加 ---
with st.sidebar:
    st.header("➕ 本の追加")
    st.info("生成アプリで作ったZIPファイルを登録します。")
    
    uploaded_zips = st.file_uploader("ZIPファイルをドロップ", type="zip", accept_multiple_files=True, help="メニュー生成アプリで作成したZIPファイルをここにアップロードしてください。")
    
    if uploaded_zips:
        count = 0
        for zfile in uploaded_zips:
            # ファイル名から店名を抽出
            filename = os.path.splitext(zfile.name)[0]
            store_name = re.sub(r'_\d{8}.*', '', filename).replace("_", " ")
            
            # 重複チェックしつつ保存
            if store_name not in st.session_state.my_library:
                st.session_state.my_library[store_name] = zfile
                count += 1
        
        if count > 0:
            st.success(f"{count}冊を追加しました！")

    st.divider()
    if st.button("🗑️ 本棚を空にする"):
        st.session_state.my_library = {}
        st.session_state.selected_shop = None
        st.rerun()

# --- プレイヤー生成関数（アクセシビリティ強化版） ---
def render_player(shop_name):
    zfile = st.session_state.my_library[shop_name]
    playlist_data = []
    map_url = None 

    try:
        with zipfile.ZipFile(zfile) as z:
            file_list = sorted(z.namelist())
            
            # HTMLファイルから地図URLを探す
            for f in file_list:
                if f.endswith(".html"):
                    try:
                        html_content = z.read(f).decode('utf-8')
                        match = re.search(r'href="(https://.*?maps.*?)"', html_content)
                        if match:
                            map_url = match.group(1)
                    except: pass

            # 音声ファイルの読み込み
            for f in file_list:
                if f.endswith(".mp3"):
                    data = z.read(f)
                    b64_data = base64.b64encode(data).decode()
                    title = f.replace(".mp3", "").replace("_", " ")
                    title = re.sub(r'^\d{2}\s*', '', title) 
                    playlist_data.append({"title": title, "src": f"data:audio/mp3;base64,{b64_data}"})
                    
    except Exception as e:
        st.error(f"ファイルの読み込みエラー: {e}"); return

    playlist_json = json.dumps(playlist_data, ensure_ascii=False)

    # 地図ボタンHTML
    map_btn_html = ""
    if map_url:
        map_btn_html = f"""
        <div style="margin: 15px 0;">
            <a href="{map_url}" target="_blank" role="button" aria-label="地図・アクセス（Googleマップが別タブで開きます）" class="map-btn">
                🗺️ Googleマップを開く
            </a>
        </div>
        """

    # アクセシビリティ対応HTMLテンプレート
    html_template = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="UTF-8">
<style>
    body { font-family: sans-serif; background-color: #f9f9f9; padding: 10px; margin: 0; }
    .player-container { 
        border: 2px solid #e0e0e0; 
        border-radius: 15px; 
        padding: 20px; 
        background-color: #ffffff; 
        text-align: center; 
        max-width: 600px; 
        margin: 0 auto; 
    }
    /* 読み上げタイトル */
    .track-title { 
        font-size: 20px; 
        font-weight: bold; 
        color: #333; 
        margin-bottom: 20px; 
        padding: 15px; 
        background: #fff; 
        border-radius: 8px; 
        border-left: 6px solid #ff4b4b; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    /* コントロールボタン */
    .controls { display: flex; gap: 10px; margin: 20px 0; }
    button.ctrl-btn { 
        flex: 1; 
        padding: 15px 0; 
        font-size: 24px; /* アイコンサイズ拡大 */
        font-weight: bold; 
        color: white; 
        background-color: #ff4b4b; 
        border: none; 
        border-radius: 8px; 
        cursor: pointer; 
        min-height: 60px; /* タップ領域確保 */
        line-height: 1;
    }
    button.ctrl-btn:hover { background-color: #e04141; }
    
    /* 地図ボタン */
    .map-btn {
        display: inline-block;
        width: 100%;
        box-sizing: border-box;
        padding: 15px;
        background: #4285F4;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        text-decoration: none;
        cursor: pointer;
        font-size: 16px;
    }
    
    /* フォーカス時のスタイル（重要） */
    button:focus, .map-btn:focus, .track-item:focus, select:focus {
        outline: 3px solid #333;
        outline-offset: 2px;
    }

    /* リスト */
    .track-list { 
        margin-top: 25px; 
        text-align: left; 
        max-height: 300px; 
        overflow-y: auto; 
        border-top: 1px solid #ddd; 
        padding-top: 10px; 
    }
    .track-item { 
        padding: 12px; 
        border-bottom: 1px solid #eee; 
        cursor: pointer; 
        font-size: 16px;
    }
    .track-item:hover { background-color: #f5f5f5; }
    
    /* アクティブ時のハイコントラスト設定 */
    .track-item.active { 
        background-color: #ffecec; 
        font-weight: bold; 
        color: #b71c1c; 
        border-left: 5px solid #ff4b4b;
    }
</style></head><body>
    <div class="player-container">
        <div class="track-title" id="title" aria-live="polite">読込中...</div>
        
        <audio id="audio" style="width:100%"></audio>
        
        <div class="controls">
            <button class="ctrl-btn" onclick="prev()" aria-label="前のチャプターへ">⏮</button>
            <button class="ctrl-btn" onclick="toggle()" id="pb" aria-label="再生">▶</button>
            <button class="ctrl-btn" onclick="next()" aria-label="次のチャプターへ">⏭</button>
        </div>
        
        __MAP_BUTTON__
        
        <div style="text-align:center; margin-top:20px;">
            <label for="speed" style="font-weight:bold; margin-right:5px;">速度:</label>
            <select id="speed" onchange="spd()" style="font-size:16px; padding:5px;">
                <option value="0.8">0.8 (ゆっくり)</option>
                <option value="1.0" selected>1.0 (標準)</option>
                <option value="1.2">1.2 (少し速く)</option>
                <option value="1.5">1.5 (速く)</option>
            </select>
        </div>
        
        <h3 style="margin-top:20px; margin-bottom:10px; color:#555;">チャプター一覧</h3>
        <div class="track-list" id="list" role="list" aria-label="チャプターリスト"></div>
    </div>
    <script>
        const pl = __PLAYLIST__; let idx = 0;
        const au = document.getElementById('audio'); 
        const ti = document.getElementById('title'); 
        const btn = document.getElementById('pb'); 
        const ls = document.getElementById('list');
        
        function init() { render(); load(0); spd(); }
        
        function load(i) { 
            idx = i; 
            au.src = pl[idx].src; 
            ti.innerText = pl[idx].title; 
            highlight(); 
            spd(); 
        }
        
        function toggle() { 
            if(au.paused){
                au.play(); 
                btn.innerText="⏸";
                btn.setAttribute("aria-label", "一時停止");
            } else {
                au.pause(); 
                btn.innerText="▶";
                btn.setAttribute("aria-label", "再生");
            } 
        }
        
        function next() { 
            if(idx < pl.length-1) { 
                load(idx+1); au.play(); 
                btn.innerText="⏸"; 
                btn.setAttribute("aria-label", "一時停止");
            } 
        }
        
        function prev() { 
            if(idx > 0) { 
                load(idx-1); au.play(); 
                btn.innerText="⏸"; 
                btn.setAttribute("aria-label", "一時停止");
            } 
        }
        
        function spd() { au.playbackRate = parseFloat(document.getElementById('speed').value); }
        
        au.onended = function() { 
            if (idx < pl.length-1) { next(); } 
            else { 
                btn.innerText="▶"; 
                btn.setAttribute("aria-label", "再生");
            } 
        };
        
        function render() { 
            ls.innerHTML = ""; 
            pl.forEach((t, i) => { 
                const d = document.createElement('div'); 
                d.className = "track-item"; 
                d.id = "tr-" + i; 
                d.innerText = (i+1) + ". " + t.title; 
                
                // アクセシビリティ属性
                d.setAttribute("role", "listitem");
                d.setAttribute("tabindex", "0"); // キーボードフォーカス可能に
                d.setAttribute("aria-label", (i+1) + "番、" + t.title);
                
                // クリック再生
                d.onclick = () => { 
                    load(i); au.play(); 
                    btn.innerText="⏸"; 
                    btn.setAttribute("aria-label", "一時停止");
                }; 
                
                // キーボード操作（Enter/Space）
                d.onkeydown = (e) => {
                    if(e.key === 'Enter' || e.key === ' '){
                        e.preventDefault();
                        d.click();
                    }
                };
                
                ls.appendChild(d); 
            }); 
        }
        
        function highlight() { 
            document.querySelectorAll('.track-item').forEach(e => e.classList.remove('active')); 
            const el = document.getElementById("tr-" + idx); 
            if(el) { 
                el.classList.add('active'); 
                el.scrollIntoView({behavior:'smooth', block:'nearest'}); 
            } 
        }
        init();
    </script></body></html>"""
    
    final_html = html_template.replace("__PLAYLIST__", playlist_json).replace("__MAP_BUTTON__", map_btn_html)
    st.components.v1.html(final_html, height=700) # 高さを少し余裕を持たせる

# --- 画面表示ロジック ---
if 'selected_shop' not in st.session_state:
    st.session_state.selected_shop = None

if st.session_state.selected_shop:
    shop_name = st.session_state.selected_shop
    
    # 戻るボタン（aria-label等はStreamlit標準だが、ラベルを明確に）
    if st.button("⬅️ 本棚に戻る", use_container_width=True):
        st.session_state.selected_shop = None
        st.rerun()
        
    st.markdown(f"### 🎧 再生中: {shop_name}")
    st.markdown("---")
    render_player(shop_name)
    
else:
    st.markdown("#### 📚 本棚")
    search_query = st.text_input("🔍 お店を検索", placeholder="店名を入力...")
    
    if not st.session_state.my_library:
        st.info("👈 左のサイドバーにZIPファイルをアップロードしてください。")
    
    shop_list = list(st.session_state.my_library.keys())
    if search_query:
        shop_list = [name for name in shop_list if search_query in name]
    
    # リスト表示
    if shop_list:
        st.write(f"全 {len(shop_list)} 冊のメニューがあります。")
        for shop_name in shop_list:
            # スクリーンリーダー向けに「を開く」を明示
            if st.button(f"📖 {shop_name} を開く", use_container_width=True):
                st.session_state.selected_shop = shop_name
                st.rerun()
