# -*- coding: utf-8 -*-
"""
週ごとの復習ページを発行するスクリプト。

archive.json から問題を5問取り出し、毎日のクイズ（index.html）と同じ
3パート構成（① 音声だけ → ② 中国語テキスト → ③ 日本語訳）の
復習ページ（{yyyymmdd}.html）を作ります。

その週の月〜金の5問は、archive.json の「日付」を見て自動で選びます。

使い方:
    # 今週分（直近の土曜日）のページを作る ← ふだんはこれだけでOK
    python3 make_review.py

    # 土曜日を指定して作る（過去の週を作り直したいときなど）
    python3 make_review.py --date 2026-07-25

引数:
    --date   発行する土曜日の日付 YYYY-MM-DD（省略時は直近の土曜日）
             ファイル名は YYYYMMDD.html になります
"""

import argparse
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# index.html と同じスタイル
CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Noto+Sans+SC:wght@400;700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: 'Noto Sans JP', sans-serif;
    background: linear-gradient(135deg, #c0392b 0%, #e74c3c 50%, #f39c12 100%);
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center; padding: 20px;
  }
  .container {
    background: white; border-radius: 24px; padding: 36px 32px;
    max-width: 480px; width: 100%;
    box-shadow: 0 20px 60px rgba(0,0,0,0.25);
  }
  .header { text-align: center; margin-bottom: 20px; }
  .header h1 { font-size: 1.2rem; color: #c0392b; font-weight: 700; letter-spacing: 0.05em; }
  .header p  { font-size: 0.78rem; color: #999; margin-top: 4px; }
  .phase-badge {
    display: inline-block; padding: 4px 14px; border-radius: 99px;
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; margin-bottom: 16px;
  }
  .phase-badge.listening { background: #fdecea; color: #c0392b; }
  .phase-badge.reading   { background: #eaf4fb; color: #2980b9; }
  .phase-badge.japanese  { background: #eafaf1; color: #27ae60; }
  .progress-bar { background: #f0f0f0; border-radius: 99px; height: 7px; margin-bottom: 22px; overflow: hidden; }
  .progress-fill { background: linear-gradient(90deg, #c0392b, #f39c12); height: 100%; border-radius: 99px; transition: width 0.4s ease; }
  .question-num { font-size: 0.72rem; color: #c0392b; font-weight: 700; letter-spacing: 0.1em; margin-bottom: 8px; }
  .instruction  { font-size: 0.88rem; color: #555; margin-bottom: 20px; line-height: 1.7; text-align: center; }
  .listen-btn {
    display: flex; align-items: center; justify-content: center; gap: 10px;
    width: 100%; padding: 18px;
    background: linear-gradient(135deg, #c0392b, #e74c3c);
    color: white; border: none; border-radius: 16px;
    font-size: 1rem; font-weight: 700; cursor: pointer;
    transition: all 0.2s; margin-bottom: 24px;
    font-family: inherit; letter-spacing: 0.05em;
  }
  .listen-btn:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(192,57,43,0.35); }
  .listen-btn.playing { background: linear-gradient(135deg, #e67e22, #f39c12); }
  .question-card {
    border-radius: 16px; padding: 20px; margin-bottom: 24px; text-align: center;
  }
  .question-card.reading-card  { background: #f8fbff; border: 2px solid #d6eaf8; }
  .question-card.japanese-card { background: #f0faf4; border: 2px solid #a9dfbf; }
  .question-card .chinese {
    font-family: 'Noto Sans SC', sans-serif;
    font-size: 1.05rem; color: #2c3e50; line-height: 1.9; margin-bottom: 8px; text-align: left;
  }
  .question-card .pinyin-text { font-size: 0.74rem; color: #7f8c8d; line-height: 1.9; margin-bottom: 8px; text-align: left; }
  .question-card .japanese-text { font-size: 0.85rem; color: #27ae60; font-weight: 700; line-height: 1.7; text-align: left; }
  .choices { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px; }
  .choice-btn {
    padding: 14px 8px; border: 2px solid #e8e8e8; border-radius: 14px;
    background: white; cursor: pointer; transition: all 0.2s;
    color: #333; font-weight: 500; line-height: 1.5; text-align: center;
  }
  .choice-btn .ch { font-family: 'Noto Sans SC', sans-serif; font-size: 1.05rem; display: block; }
  .choice-btn .py { font-size: 0.65rem; color: #aaa; display: block; margin-top: 2px; }
  .choice-btn .ja { font-size: 0.72rem; color: #888; display: block; margin-top: 3px; }
  .choice-btn:hover:not(:disabled) { border-color: #c0392b; background: #fff5f5; transform: translateY(-1px); }
  .choice-btn.correct { border-color: #27ae60; background: #eafaf1; }
  .choice-btn.correct .ch { color: #27ae60; }
  .choice-btn.wrong   { border-color: #e74c3c; background: #fdedec; }
  .choice-btn.wrong .ch { color: #e74c3c; }
  .choice-btn:disabled { cursor: not-allowed; }
  .feedback {
    text-align: center; padding: 14px; border-radius: 12px;
    font-size: 0.92rem; font-weight: 700; margin-bottom: 16px;
    display: none; animation: fadeIn 0.3s ease; line-height: 1.6;
  }
  .feedback.correct { background: #eafaf1; color: #27ae60; }
  .feedback.wrong   { background: #fdedec; color: #e74c3c; }
  @keyframes fadeIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
  .next-btn {
    width: 100%; padding: 15px; background: #2c3e50; color: white;
    border: none; border-radius: 14px; font-size: 0.95rem; font-weight: 700;
    cursor: pointer; transition: all 0.2s; font-family: inherit;
    display: none; letter-spacing: 0.05em; margin-bottom: 10px;
  }
  .next-btn:hover { background: #34495e; transform: translateY(-1px); }
  .switch-btn {
    width: 100%; padding: 14px;
    background: linear-gradient(135deg, #2980b9, #3498db);
    color: white; border: none; border-radius: 14px;
    font-size: 0.88rem; font-weight: 700; cursor: pointer;
    transition: all 0.2s; font-family: inherit; display: none; margin-bottom: 8px;
  }
  .switch-btn:hover { transform: translateY(-1px); }
  .switch-btn2 {
    width: 100%; padding: 14px;
    background: linear-gradient(135deg, #27ae60, #2ecc71);
    color: white; border: none; border-radius: 14px;
    font-size: 0.88rem; font-weight: 700; cursor: pointer;
    transition: all 0.2s; font-family: inherit; display: none;
  }
  .switch-btn2:hover { transform: translateY(-1px); }
  .end-btn {
    width: 100%; padding: 12px;
    background: white; color: #999;
    border: 2px solid #ddd; border-radius: 14px;
    font-size: 0.85rem; font-weight: 700; cursor: pointer;
    transition: all 0.2s; font-family: inherit; display: none; margin-bottom: 8px;
  }
  .end-btn:hover { background: #f9f9f9; border-color: #bbb; color: #666; }
  .hint { font-size: 0.72rem; color: #ccc; text-align: center; margin-top: 12px; }
  .result-screen { display: none; text-align: center; }
  .result-title  { font-size: 1.3rem; font-weight: 700; color: #2c3e50; margin-bottom: 6px; }
  .answer-row { display: flex; align-items: center; gap: 10px; padding: 12px 0; border-bottom: 1px solid #f0f0f0; text-align: left; }
  .answer-row:last-child { border-bottom: none; }
  .answer-num { font-size: 0.75rem; font-weight: 700; color: #c0392b; min-width: 28px; }
  .answer-ch  { font-family: 'Noto Sans SC', sans-serif; font-size: 1.4rem; font-weight: 700; color: #2c3e50; min-width: 60px; }
  .answer-py  { font-size: 0.75rem; color: #7f8c8d; min-width: 80px; }
  .answer-ja  { font-size: 0.85rem; font-weight: 700; color: #27ae60; }
  .retry-btn {
    width: 100%; padding: 13px; background: white; color: #c0392b;
    border: 2px solid #c0392b; border-radius: 14px;
    font-size: 0.9rem; font-weight: 700; cursor: pointer;
    transition: all 0.2s; font-family: inherit; margin-top: 18px;
  }
  .retry-btn:hover { background: #fff5f5; }
"""

# index.html と同じ 3 パート構成のロジック。
# 違いは音声を questions[].audio から読む点だけ。
SCRIPT = r"""
const questions = __QUESTIONS__;

let current        = 0;
let score          = 0;
let listeningScore = 0;
let readingScore   = 0;
let japaneseScore  = 0;
let answered       = false;
let currentAudio   = null;

const N     = questions.length;
const TOTAL = N * 3;

// 1問につき 音声(0) → テキスト(1) → 日本語訳(2) の3パートを連続表示する。
// current = 問題番号 * 3 + パート番号
function getPhase() {
  var sub = current % 3;
  return sub === 0 ? 'listening' : sub === 1 ? 'reading' : 'japanese';
}
function questionIndex() { return Math.floor(current / 3); }

function playAudio() {
  const btn     = document.getElementById('listenBtn');
  const btnText = document.getElementById('listenBtnText');
  if (currentAudio && !currentAudio.paused) {
    currentAudio.pause();
    btn.classList.remove('playing');
    btnText.textContent = '▶ 続きから再生';
    return;
  }
  if (currentAudio && currentAudio.paused && currentAudio.currentTime > 0) {
    btn.classList.add('playing');
    btnText.textContent = '⏸ 停止する';
    currentAudio.play();
    return;
  }
  if (currentAudio) { currentAudio.pause(); currentAudio.currentTime = 0; }
  currentAudio = new Audio(questions[questionIndex()].audio);
  currentAudio.volume = 1.0;
  btn.classList.add('playing');
  btnText.textContent = '⏸ 停止する';
  const p = currentAudio.play();
  if (p !== undefined) {
    p.catch(err => {
      console.warn('play error:', err);
      btn.classList.remove('playing');
      btnText.textContent = '音声を再生する';
    });
  }
  currentAudio.onended = () => {
    btn.classList.remove('playing');
    btnText.textContent = 'もう一度聞く 🔄';
  };
}

function playCorrectSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const now = ctx.currentTime;
    function ping(freq, startTime, duration) {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.type = 'sine';
      o.frequency.setValueAtTime(freq, startTime);
      o.frequency.exponentialRampToValueAtTime(freq * 0.98, startTime + duration);
      g.gain.setValueAtTime(0, startTime);
      g.gain.linearRampToValueAtTime(0.5, startTime + 0.01);
      g.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
      o.start(startTime);
      o.stop(startTime + duration);
    }
    ping(1046, now,        0.45);
    ping(1318, now + 0.02, 0.40);
    ping(784,  now + 0.22, 0.55);
    ping(659,  now + 0.24, 0.50);
  } catch(e) {}
}

function playWrongSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [[200,0],[180,0.22]].forEach(([freq,t]) => {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.frequency.value = freq; o.type = 'sawtooth';
      const st = ctx.currentTime + t;
      g.gain.setValueAtTime(0.3, st);
      g.gain.exponentialRampToValueAtTime(0.001, st + 0.28);
      o.start(st); o.stop(st + 0.28);
    });
  } catch(e) {}
}

function speakChinese(text) {
  if (!window.speechSynthesis) return;
  speechSynthesis.cancel();
  var utter = new SpeechSynthesisUtterance(text);
  utter.lang = 'zh-CN';
  utter.rate = 0.85;
  speechSynthesis.speak(utter);
}

function renderQuestion() {
  answered = false;
  const phase = getPhase();
  const q     = questions[questionIndex()];

  if (currentAudio) { currentAudio.pause(); currentAudio.currentTime = 0; currentAudio = null; }

  const badge  = document.getElementById('phaseBadge');
  const labels = { listening:'🔊 リスニングパート', reading:'📖 テキストパート', japanese:'📝 日本語訳パート' };
  badge.textContent = labels[phase];
  badge.className   = 'phase-badge ' + phase;

  document.getElementById('progressFill').style.width = (current / TOTAL * 100) + '%';
  document.getElementById('questionNum').textContent  = '問題 ' + (questionIndex() + 1) + ' / ' + N + '　' + {listening:'🔊',reading:'📖',japanese:'📝'}[phase];

  document.getElementById('feedback').style.display   = 'none';
  document.getElementById('nextBtn').style.display    = 'none';
  document.getElementById('switchBtn').style.display  = 'none';
  document.getElementById('switchBtn2').style.display = 'none';
  document.getElementById('skipBtn').style.display    = 'none';

  var listenBtn    = document.getElementById('listenBtn');
  var readingCard  = document.getElementById('readingCard');
  var japaneseCard = document.getElementById('japaneseCard');

  if (phase === 'listening') {
    listenBtn.style.display    = 'flex';
    readingCard.style.display  = 'none';
    japaneseCard.style.display = 'none';
    listenBtn.classList.remove('playing');
    document.getElementById('listenBtnText').textContent = '音声を再生する';
    document.getElementById('instruction').textContent   = '音声を聞いて、何について説明しているか選んでください。';
    document.getElementById('hintText').textContent      = '※ まず音声を聞いてから選んでみよう';
  } else if (phase === 'reading') {
    listenBtn.style.display    = 'flex';
    listenBtn.classList.remove('playing');
    document.getElementById('listenBtnText').textContent = '音声を再生する';
    readingCard.style.display  = 'block';
    japaneseCard.style.display = 'none';
    document.getElementById('readingChinese').innerText = q.text;
    document.getElementById('readingPinyin').innerText  = q.pinyin;
    document.getElementById('instruction').textContent  = '問題文を読んで、何について説明しているか選んでください。';
    document.getElementById('hintText').textContent     = '';
  } else {
    listenBtn.style.display    = 'flex';
    listenBtn.classList.remove('playing');
    document.getElementById('listenBtnText').textContent = '音声を再生する';
    readingCard.style.display  = 'none';
    japaneseCard.style.display = 'block';
    document.getElementById('japaneseChinese').innerText     = q.text;
    document.getElementById('japanesePinyin').innerText      = q.pinyin;
    document.getElementById('japaneseTranslation').innerText = q.japanese;
    document.getElementById('instruction').textContent       = '問題文を読んで、正しい答えを選んでください。';
    document.getElementById('hintText').textContent          = '';
  }

  var choicesDiv = document.getElementById('choices');
  choicesDiv.innerHTML = '';
  for (var i = 0; i < q.choices.length; i++) {
    var c   = q.choices[i];
    var btn = document.createElement('button');
    btn.className = 'choice-btn';
    if (phase === 'japanese') {
      btn.innerHTML = '<span class="ch">' + c.ch + '</span><span class="py">' + c.py + '</span><span class="ja">' + c.ja + '</span>';
    } else {
      btn.innerHTML = '<span class="ch">' + c.ch + '</span><span class="py">' + c.py + '</span>';
    }
    (function(idx) { btn.onclick = function() { selectAnswer(idx); }; })(i);
    choicesDiv.appendChild(btn);
  }
}

function selectAnswer(index) {
  if (answered) return;
  answered = true;

  var phase    = getPhase();
  var q        = questions[questionIndex()];
  speakChinese(q.choices[index].ch);
  var buttons  = document.querySelectorAll('.choice-btn');
  var feedback = document.getElementById('feedback');

  for (var i = 0; i < buttons.length; i++) { buttons[i].disabled = true; }
  buttons[q.correctIndex].classList.add('correct');

  if (index === q.correctIndex) {
    feedback.innerHTML = '✅ 正解！「' + q.answer + '（' + q.answerPinyin + '）' + q.answerJapanese + '」';
    feedback.className = 'feedback correct';
    score++;
    if (phase === 'listening') listeningScore++;
    else if (phase === 'reading') readingScore++;
    else japaneseScore++;
    playCorrectSound();
  } else {
    buttons[index].classList.add('wrong');
    feedback.innerHTML = '❌ 不正解… 正解は「' + q.answer + '（' + q.answerPinyin + '）' + q.answerJapanese + '」';
    feedback.className = 'feedback wrong';
    playWrongSound();
  }
  feedback.style.display = 'block';

  var nextBtn    = document.getElementById('nextBtn');
  var switchBtn  = document.getElementById('switchBtn');
  var switchBtn2 = document.getElementById('switchBtn2');
  var sub        = current % 3;

  // スキップ先が結果画面になる（＝最後の問題）かどうかでボタン文言を変える
  var skipBtn = document.getElementById('skipBtn');
  skipBtn.textContent = (questionIndex() === N - 1) ? '⏭ 結果を見る' : '⏭ 次の問題へ';

  if (sub === 0) {
    // 音声パート → 中国語テキストへ（または次の問題へスキップ）
    switchBtn.style.display = 'block';
    skipBtn.style.display = 'block';
    document.getElementById('hintText').textContent = '';
  } else if (sub === 1) {
    // テキストパート → 日本語訳へ（または次の問題へスキップ）
    switchBtn2.style.display = 'block';
    skipBtn.style.display = 'block';
  } else {
    // 日本語訳パート → 次の問題へ（最後なら結果へ）
    nextBtn.style.display = 'block';
    nextBtn.textContent   = (current === TOTAL - 1) ? '結果を見る 🎉' : '次の問題へ →';
  }
}

function nextQuestion() {
  current++;
  if (current < TOTAL) renderQuestion();
  else               showResult();
}

// 残りのパートを飛ばして次の問題（の音声パート）へ進む
function skipToNextQuestion() {
  current = (questionIndex() + 1) * 3;
  if (current < TOTAL) renderQuestion();
  else                 showResult();
}

function showResult() {
  if (currentAudio) { currentAudio.pause(); currentAudio.currentTime = 0; currentAudio = null; }
  document.getElementById('progressFill').style.width   = '100%';
  document.getElementById('quizScreen').style.display   = 'none';
  document.getElementById('resultScreen').style.display = 'block';
  var html = '';
  questions.forEach(function(q, i) {
    html += '<div class="answer-row">'
          + '<span class="answer-num">Q' + (i+1) + '</span>'
          + '<span class="answer-ch">' + q.answer + '</span>'
          + '<span class="answer-py">' + q.answerPinyin + '</span>'
          + '<span class="answer-ja">' + q.answerJapanese + '</span>'
          + '</div>';
  });
  document.getElementById('resultAnswers').innerHTML = html;
}

function restartQuiz() {
  current = 0; score = 0; listeningScore = 0; readingScore = 0; japaneseScore = 0;
  document.getElementById('resultScreen').style.display = 'none';
  document.getElementById('quizScreen').style.display   = 'block';
  renderQuestion();
}

renderQuestion();
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🇨🇳 中国語クイズ 復習（__DATE_JP__）</title>
<style>__CSS__</style>
</head>
<body>
<div class="container">
  <div id="quizScreen">
    <div class="header">
      <h1>🇨🇳 中国語クイズ 復習</h1>
      <p>__DATE_JP__ の週のまとめ　リスニング・テキスト・日本語訳　全3パート</p>
    </div>
    <div class="progress-bar">
      <div class="progress-fill" id="progressFill" style="width:0%"></div>
    </div>
    <div style="text-align:center">
      <span class="phase-badge listening" id="phaseBadge">🔊 リスニングパート</span>
    </div>
    <div class="question-num" id="questionNum">問題 1 / __N__</div>
    <div class="instruction" id="instruction">音声を聞いて、何について説明しているか選んでください。</div>

    <button class="listen-btn" id="listenBtn" onclick="playAudio()">
      <span>🔊</span><span id="listenBtnText">音声を再生する</span>
    </button>

    <div class="question-card reading-card" id="readingCard" style="display:none">
      <div class="chinese" id="readingChinese"></div>
      <div class="pinyin-text" id="readingPinyin"></div>
    </div>
    <div class="question-card japanese-card" id="japaneseCard" style="display:none">
      <div class="chinese" id="japaneseChinese"></div>
      <div class="pinyin-text" id="japanesePinyin"></div>
      <div class="japanese-text" id="japaneseTranslation"></div>
    </div>

    <div class="choices" id="choices"></div>

    <div class="feedback" id="feedback"></div>
    <button class="next-btn"    id="nextBtn"    onclick="nextQuestion()">次の問題へ →</button>
    <button class="switch-btn"  id="switchBtn"  onclick="nextQuestion()">📖 テキストで確認</button>
    <button class="switch-btn2" id="switchBtn2" onclick="nextQuestion()">📝 日本語を確認</button>
    <button class="end-btn" id="skipBtn" onclick="skipToNextQuestion()" style="display:none">⏭ 次の問題へ</button>
    <p class="hint" id="hintText">※ まず音声を聞いてから選んでみよう</p>
  </div>

  <div class="result-screen" id="resultScreen">
    <div class="result-title">✅ 正解</div>
    <div id="resultAnswers"></div>
    <button class="retry-btn" onclick="restartQuiz()">🔄 もう一度挑戦する</button>
  </div>
</div>

<script>
__SCRIPT__
</script>
</body>
</html>
"""


WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]


def resolve_saturday(date_str):
    """発行日（土曜日）を決める。省略時は「今日を含む直近の土曜日」。"""
    if date_str:
        try:
            d = datetime.date.fromisoformat(date_str)
        except ValueError:
            raise SystemExit("日付は YYYY-MM-DD の形式で指定してください（例 2026-08-01）")
        if d.weekday() != 5:
            print("※ 注意: {} は{}曜日です（土曜日ではありません）".format(
                d.isoformat(), WEEKDAY_JP[d.weekday()]))
        return d
    today = datetime.date.today()
    # 今日が土曜ならそのまま。それ以外は直前の土曜まで戻る。
    return today - datetime.timedelta(days=(today.weekday() - 5) % 7)


def pick_week_questions(archive, saturday):
    """その週の月〜金（土曜の5日前〜1日前）の問題を日付で選ぶ。"""
    monday = saturday - datetime.timedelta(days=5)
    wanted = [monday + datetime.timedelta(days=i) for i in range(5)]

    by_date = {}
    for q in archive:
        by_date.setdefault(q["date"], q)

    selected, missing = [], []
    for d in wanted:
        key = d.isoformat()
        if key in by_date:
            selected.append(by_date[key])
        else:
            missing.append("{}（{}）".format(key, WEEKDAY_JP[d.weekday()]))

    if missing:
        raise SystemExit(
            "archive.json に次の日の問題が見つかりません:\n  - "
            + "\n  - ".join(missing)
            + "\n\n（毎日のクイズがまだ登録されていない可能性があります）"
        )
    return selected


def build(date_str=None, count=5):
    with open(os.path.join(HERE, "archive.json"), encoding="utf-8") as f:
        archive = json.load(f)

    saturday = resolve_saturday(date_str)
    selected = pick_week_questions(archive, saturday)

    # archive.json では改行が「\n」という2文字で保存されているので、
    # 実際の改行に直して表示する（毎日のクイズと同じ挙動にそろえる）。
    def nl(s):
        return s.replace("\\n", "\n")

    questions = []
    for q in selected:
        questions.append({
            "text": nl(q["text"]),
            "pinyin": nl(q["pinyin"]),
            "japanese": nl(q["japanese"]),
            "answer": q["answer"],
            "answerPinyin": q["answerPinyin"],
            "answerJapanese": q["answerJapanese"],
            "choices": q["choices"],
            "correctIndex": q["correctIndex"],
            "audio": q["audio"],
        })

    questions_json = json.dumps(questions, ensure_ascii=False)
    script = SCRIPT.replace("__QUESTIONS__", questions_json)

    date_jp = "{}/{}/{}".format(saturday.year, saturday.month, saturday.day)

    html = (HTML_TEMPLATE
            .replace("__CSS__", CSS)
            .replace("__SCRIPT__", script)
            .replace("__DATE_JP__", date_jp)
            .replace("__N__", str(len(questions))))

    out_name = saturday.strftime("%Y%m%d") + ".html"
    out_path = os.path.join(HERE, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print("作成しました: {}（{} 問 × 3パート）".format(out_name, len(questions)))
    print("内容:")
    for q, orig in zip(questions, selected):
        d = datetime.date.fromisoformat(orig["date"])
        print("  {}（{}） {} … {}".format(
            d.strftime("%-m/%-d"), WEEKDAY_JP[d.weekday()], q["answer"], q["answerJapanese"]))
    return out_path


def main():
    p = argparse.ArgumentParser(
        description="週ごとの復習ページを発行します（その週の月〜金5問を日付で自動選択）")
    p.add_argument("--date", default=None,
                   help="発行する土曜日 YYYY-MM-DD（省略時は直近の土曜日）")
    args = p.parse_args()
    build(args.date)


if __name__ == "__main__":
    main()
