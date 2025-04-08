import streamlit as st
import pypdf
import re
from streamlit.components.v1 import html

st.set_page_config(page_title="PDF Text Extractor", layout="wide")

# CSSスタイルの設定（余白やボタンのデザイン調整）
st.markdown("""
<style>
    .stExpander {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }
    .streamlit-expanderContent {
        margin-top: 0px !important;
        padding-top: 0px !important;
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
    .stTextArea {
        margin-bottom: 0px !important;
    }
    /* テキストエリアとボタンを横並びにするスタイル */
    .text-with-button {
        display: flex;
        align-items: flex-start;
        margin-bottom: 5px;
        width: 100%;
    }
    .copy-button {
        padding: 5px 10px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        height: fit-content;
        margin-right: 10px;
        min-width: 80px;
        flex-shrink: 0;
    }
    .copy-button:hover {
        background-color: #45a049;
    }
    .remove-newline-button {
        padding: 5px 10px;
        background-color: #2196F3;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        height: fit-content;
        margin-right: 10px;
        min-width: 100px;
        flex-shrink: 0;
    }
    .remove-newline-button:hover {
        background-color: #0b7dda;
    }
    .text-area-container {
        flex-grow: 1;
        width: calc(100% - 200px);
    }
    .text-area-container textarea {
        width: 100%;
        resize: vertical;
        min-width: 500px;
    }
</style>
""", unsafe_allow_html=True)

st.title("PDFテキスト抽出 & コピー可能なブロック表示")
st.write("PDFファイルをアップロードして、テキストを空白行で区切られたブロックとして表示します。各ブロックは選択してコピーできます。")

uploaded_file = st.file_uploader("PDFファイルをアップロード", type="pdf")

def extract_text_from_pdf(file):
    pdf_reader = pypdf.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def split_text_by_blank_lines(text):
    # 一行以上の空白行で分割
    blocks = re.split(r'\n\s*\n+', text)
    # 空のブロックを削除
    blocks = [block.strip() for block in blocks if block.strip()]
    return blocks

# 改行を空白に置き換える関数
def remove_newlines(text):
    return re.sub(r'\r?\n', ' ', text)

# クリップボードコピー用のHTMLコンポーネント（個別ブロック用）
def text_with_copy_button(text, key):
    # 事前に改行を削除したテキストを用意
    text_without_newlines = remove_newlines(text)
    
    newline_count = text.count('\n')
    # 改行数に応じた高さを計算（最小値を設定）
    height = max(80, 30 + 20 * newline_count)
    
    component_html = f"""
    <div class="text-with-button">
        <button class="copy-button" data-target="text_{key}">コピー</button>
        <button class="remove-newline-button" data-target="text_{key}" data-no-newlines="{text_without_newlines}">改行削除</button>
        <div class="text-area-container">
            <textarea id="text_{key}" style="height: {height}px; padding: 8px; width: 100%;">{text}</textarea>
        </div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', (event) => {{
        // コピーボタンの処理
        document.querySelectorAll('.copy-button').forEach(button => {{
            button.addEventListener('click', () => {{
                const elementId = button.getAttribute('data-target');
                const textarea = document.getElementById(elementId);
                navigator.clipboard.writeText(textarea.value).then(() => {{
                    button.textContent = 'コピー完了!';
                    setTimeout(() => button.textContent = 'コピー', 2000);
                }}).catch(err => console.error('コピーに失敗しました:', err));
            }});
        }});

        // 改行削除ボタンの処理
        document.querySelectorAll('.remove-newline-button').forEach(button => {{
            button.addEventListener('click', () => {{
                const elementId = button.getAttribute('data-target');
                const textarea = document.getElementById(elementId);
                const textWithoutNewlines = button.getAttribute('data-no-newlines');
                
                // 元のテキストを保存（ない場合は作成）
                if (!textarea.hasAttribute('data-original-text')) {{
                    textarea.setAttribute('data-original-text', textarea.value);
                }}
                
                // 改行削除テキストを表示
                textarea.value = textWithoutNewlines;
                
                // ボタンのテキストを変更し、元に戻すボタンにする
                button.textContent = '元に戻す';
                button.classList.remove('remove-newline-button');
                button.classList.add('restore-button');
                button.style.backgroundColor = '#FF9800';
                
                // クリップボードにコピー
                navigator.clipboard.writeText(textWithoutNewlines).catch(err => 
                    console.error('コピーに失敗しました:', err));
            }});
        }});
        
        // イベント委譲で元に戻すボタンのクリックを処理
        document.addEventListener('click', (event) => {{
            if (event.target.classList.contains('restore-button')) {{
                const elementId = event.target.getAttribute('data-target');
                const textarea = document.getElementById(elementId);
                const originalText = textarea.getAttribute('data-original-text');
                
                // 元のテキストに戻す
                textarea.value = originalText;
                
                // ボタンを元の状態に戻す
                event.target.textContent = '改行削除';
                event.target.classList.remove('restore-button');
                event.target.classList.add('remove-newline-button');
                event.target.style.backgroundColor = '#2196F3';
            }}
        }});
    }});
    </script>
    """
    
    return html(component_html, height=(height + 40))

# 全テキストのコピー用のHTMLコンポーネント
def all_text_with_copy_button(text, key="all_text"):
    # 事前に改行を削除したテキストを用意
    text_without_newlines = remove_newlines(text)
    
    component_html = f"""
    <div class="text-with-button">
        <button class="copy-button" data-target="text_{key}">すべてコピー</button>
        <button class="remove-newline-button" data-target="text_{key}" data-no-newlines="{text_without_newlines}">改行削除</button>
        <div class="text-area-container">
            <textarea id="text_{key}" style="height: 100px; padding: 8px; width: 100%;">{text}</textarea>
        </div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', (event) => {{
        // コピーボタンの処理
        document.querySelectorAll('.copy-button').forEach(button => {{
            button.addEventListener('click', () => {{
                const elementId = button.getAttribute('data-target');
                const textarea = document.getElementById(elementId);
                navigator.clipboard.writeText(textarea.value).then(() => {{
                    button.textContent = 'コピー完了!';
                    setTimeout(() => button.textContent = 'すべてコピー', 2000);
                }}).catch(err => console.error('コピーに失敗しました:', err));
            }});
        }});

        // 改行削除ボタンの処理
        document.querySelectorAll('.remove-newline-button').forEach(button => {{
            button.addEventListener('click', () => {{
                const elementId = button.getAttribute('data-target');
                const textarea = document.getElementById(elementId);
                const textWithoutNewlines = button.getAttribute('data-no-newlines');
                
                // 元のテキストを保存（ない場合は作成）
                if (!textarea.hasAttribute('data-original-text')) {{
                    textarea.setAttribute('data-original-text', textarea.value);
                }}
                
                // 改行削除テキストを表示
                textarea.value = textWithoutNewlines;
                
                // ボタンのテキストを変更し、元に戻すボタンにする
                button.textContent = '元に戻す';
                button.classList.remove('remove-newline-button');
                button.classList.add('restore-button');
                button.style.backgroundColor = '#FF9800';
                
                // クリップボードにコピー
                navigator.clipboard.writeText(textWithoutNewlines).catch(err => 
                    console.error('コピーに失敗しました:', err));
            }});
        }});
        
        // イベント委譲で元に戻すボタンのクリックを処理
        document.addEventListener('click', (event) => {{
            if (event.target.classList.contains('restore-button')) {{
                const elementId = event.target.getAttribute('data-target');
                const textarea = document.getElementById(elementId);
                const originalText = textarea.getAttribute('data-original-text');
                
                // 元のテキストに戻す
                textarea.value = originalText;
                
                // ボタンを元の状態に戻す
                event.target.textContent = '改行削除';
                event.target.classList.remove('restore-button');
                event.target.classList.add('remove-newline-button');
                event.target.style.backgroundColor = '#2196F3';
            }}
        }});
    }});
    </script>
    """
    
    return html(component_html, height=170)

if uploaded_file is not None:
    try:
        # PDFからテキストを抽出
        text = extract_text_from_pdf(uploaded_file)
        
        # テキストブロックに分割
        blocks = split_text_by_blank_lines(text)
        
        # サイドバーにオプションを表示
        # with st.sidebar:
        #     st.header("オプション")
        #     show_line_numbers = st.checkbox("行番号を表示", value=False)
            
        #     # すべてのテキストをコピーするボタン
        #     st.write("### すべてのテキスト")
        #     all_text_with_copy_button(text)
        
        # メイン画面にブロックを表示
        st.header(f"抽出されたテキストブロック ({len(blocks)}個)")
        
        for i, block in enumerate(blocks):
            if False:
                # 行番号付きで表示する場合
                numbered_lines = []
                for j, line in enumerate(block.split("\n")):
                    numbered_lines.append(f"{j+1}: {line}")
                block_with_numbers = "\n".join(numbered_lines)
                
                col1, col2 = st.columns([1, 9])
                with col1:
                    if st.button("コピー", key=f"copy_code_{i}"):
                        st.session_state[f"copied_{i}"] = True
                with col2:
                    st.code(block_with_numbers, language=None)
                
                if f"copied_{i}" in st.session_state and st.session_state[f"copied_{i}"]:
                    st.success("コピーしました！")
                    st.session_state[f"copied_{i}"] = False
            else:
                # 通常のテキストブロック表示（ボタン付き）
                text_with_copy_button(block, f"block_{i}")
    
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
else:
    st.info("PDFファイルをアップロードしてください。")

# アプリの使い方ガイド
with st.expander("使い方"):
    st.markdown("""
    ### 使い方ガイド
    1. 左上の「PDFファイルをアップロード」ボタンからPDFファイルを選択します
    2. PDFからテキストが抽出され、空白行で区切られたブロックとして表示されます
    3. 各ブロックの左側にある「コピー」ボタンをクリックすると、テキストがクリップボードにコピーされます
    4. 「改行削除」ボタンをクリックすると、改行が空白に置き換えられた状態でテキストが表示され、自動的にクリップボードにコピーされます
    5. 改行を削除した後は「元に戻す」ボタンをクリックすると元のテキストに戻ります
    6. サイドバーの「すべてコピー」ボタンで、テキスト全体をコピーできます
    7. サイドバーのオプションで行番号表示の切り替えができます
    
    ### 注意点
    - PDFの構造によっては、テキスト抽出の精度が変わる場合があります
    - 複雑なレイアウトや画像主体のPDFでは正確に抽出できないことがあります
    """)