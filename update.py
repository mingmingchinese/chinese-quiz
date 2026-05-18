#!/usr/bin/env python3
# 使い方: python3 update.py
# today.txt を編集してからこのスクリプトを実行してください

import base64, re, os, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TODAY_FILE = os.path.join(SCRIPT_DIR, 'today.txt')
HTML_FILE  = os.path.join(SCRIPT_DIR, 'index.html')

# --- today.txt を読み込む ---
config = {}
with open(TODAY_FILE, encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, _, val = line.partition(':')
        config[key.strip()] = val.strip()

required = ['AUDIO','TEXT','PINYIN','JAPANESE','CORRECT',
            'CHOICE1_CH','CHOICE1_PY','CHOICE1_JA',
            'CHOICE2_CH','CHOICE2_PY','CHOICE2_JA',
            'CHOICE3_CH','CHOICE3_PY','CHOICE3_JA',
            'CHOICE4_CH','CHOICE4_PY','CHOICE4_JA']
for key in required:
    if key not in config:
        print(f'エラー: today.txt に {key} がありません')
        sys.exit(1)

correct_index = int(config['CORRECT']) - 1  # 0始まりに変換

choices = []
for i in range(1, 5):
    choices.append({
        'ch': config[f'CHOICE{i}_CH'],
        'py': config[f'CHOICE{i}_PY'],
        'ja': config[f'CHOICE{i}_JA'],
    })

answer = choices[correct_index]

# --- 音声ファイルをbase64に変換 ---
audio_path = config['AUDIO']
if not os.path.exists(audio_path):
    print(f'エラー: 音声ファイルが見つかりません → {audio_path}')
    sys.exit(1)

with open(audio_path, 'rb') as f:
    audio_b64 = 'data:audio/mpeg;base64,' + base64.b64encode(f.read()).decode()

print(f'音声ファイル読み込み完了: {os.path.basename(audio_path)}')

# --- index.html を読み込む ---
with open(HTML_FILE, encoding='utf-8') as f:
    html = f.read()

# --- audioData を置き換える ---
audio_start = html.find('const audioData = [')
audio_end   = html.find('];', audio_start) + 2
new_audio   = f'const audioData = [\n  "{audio_b64}"\n];'
html = html[:audio_start] + new_audio + html[audio_end:]

# --- questions を置き換える ---
choices_js = ',\n      '.join(
    f'{{ ch:"{c["ch"]}", py:"{c["py"]}", ja:"{c["ja"]}" }}' for c in choices
)
pinyin_escaped = config['PINYIN'].replace('\\n', '\\n')

new_questions = f'''const questions = [
  {{
    text: "{config['TEXT']}",
    pinyin: "{pinyin_escaped}",
    japanese: "{config['JAPANESE']}",
    answer: "{answer['ch']}", answerPinyin: "{answer['py']}", answerJapanese: "{answer['ja']}",
    choices: [
      {choices_js}
    ],
    correctIndex: {correct_index}
  }}
];'''

q_start = html.find('const questions = [')
q_end   = html.find('];', q_start) + 2
html = html[:q_start] + new_questions + html[q_end:]

# --- index.html を保存 ---
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print('index.html を更新しました！')
print(f'  問題: {config["TEXT"][:30]}...')
print(f'  正解: {answer["ch"]}（{answer["py"]}）{answer["ja"]}')
print()
print('次のステップ: ターミナルで以下を実行してGitHubにアップしてください')
print()
print('  cd ~/Downloads/chinese-quiz')
print('  git add index.html')
print('  git commit -m "問題を更新"')
print('  git push')
