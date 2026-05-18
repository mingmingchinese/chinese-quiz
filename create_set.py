#!/usr/bin/env python3
# 使い方: python3 create_set.py
# archive.json の最新5問でセットページを自動生成します

import json, os, sys

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
ARCHIVE_FILE = os.path.join(SCRIPT_DIR, 'archive.json')
HTML_FILE    = os.path.join(SCRIPT_DIR, 'index.html')

# --- archive.json を読み込む ---
if not os.path.exists(ARCHIVE_FILE):
    print('エラー: archive.json がありません。先に update.py を5回以上実行してください。')
    sys.exit(1)

with open(ARCHIVE_FILE, encoding='utf-8') as f:
    archive = json.load(f)

if len(archive) < 5:
    print(f'エラー: まだ {len(archive)} 問しかありません。5問以上必要です。')
    sys.exit(1)

# 最新5問を取得
questions = archive[-5:]
set_number = (len(archive) - 1) // 5 + 1
set_dir    = os.path.join(SCRIPT_DIR, f'set{set_number}')
os.makedirs(set_dir, exist_ok=True)

# --- index.html をテンプレートとして読み込む ---
with open(HTML_FILE, encoding='utf-8') as f:
    html = f.read()

# --- audioData を5問分に置き換える ---
audio_entries = ',\n  '.join(f'"{q["audio"]}"' for q in questions)
new_audio = f'const audioData = [\n  {audio_entries}\n];'
audio_start = html.find('const audioData = [')
audio_end   = html.find('];', audio_start) + 2
html = html[:audio_start] + new_audio + html[audio_end:]

# --- questions を5問分に置き換える ---
def q_to_js(q):
    choices_js = ',\n      '.join(
        f'{{ ch:"{c["ch"]}", py:"{c["py"]}", ja:"{c["ja"]}" }}' for c in q['choices']
    )
    return f'''  {{
    text: "{q['text']}",
    pinyin: "{q['pinyin']}",
    japanese: "{q['japanese']}",
    answer: "{q['answer']}", answerPinyin: "{q['answerPinyin']}", answerJapanese: "{q['answerJapanese']}",
    choices: [
      {choices_js}
    ],
    correctIndex: {q['correctIndex']}
  }}'''

questions_js = ',\n'.join(q_to_js(q) for q in questions)
new_questions = f'const questions = [\n{questions_js}\n];'
q_start = html.find('const questions = [')
q_end   = html.find('];', q_start) + 2
html = html[:q_start] + new_questions + html[q_end:]

# --- タイトルを変更 ---
html = html.replace(
    '🇨🇳 中国語クイズ',
    f'🇨🇳 中国語クイズ SET {set_number}'
)
html = html.replace(
    '<p>リスニング・テキスト・日本語訳　全3パート</p>',
    f'<p>リスニング・テキスト・日本語訳　全5問</p>'
)

# --- set フォルダに保存 ---
out_file = os.path.join(set_dir, 'index.html')
with open(out_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'SET {set_number} を作成しました！')
print(f'  フォルダ: set{set_number}/')
print(f'  収録問題: {", ".join(q["answer"] for q in questions)}')
print()
print('GitHubにアップしてください:')
print()
print(f'  cd ~/Downloads/chinese-quiz')
print(f'  git add set{set_number}/')
print(f'  git commit -m "SET{set_number}を追加"')
print(f'  git push')
print()
print(f'公開URL: https://mingmingchinese.github.io/chinese-quiz/set{set_number}/')
