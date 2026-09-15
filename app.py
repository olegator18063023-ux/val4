from flask import Flask, jsonify, render_template_string
import random
import time
import threading

app = Flask(__name__)

state = {
    "running": False,
    "hours": 0,
    "health": 91.0,
    "rul": 486.0,
    "failure": 4.8,
    "cycles": 12840,
    "temperature": 68.4,
    "vibration": 2.8,
    "pressure": 4.9,
    "load": 61.0,
}

history = {
    "temperature": [64 + random.random() * 7 for _ in range(30)],
    "vibration": [2 + random.random() * 0.8 for _ in range(30)],
    "load": [55 + random.random() * 12 for _ in range(30)],
}


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def add_history():
    history["temperature"].append(state["temperature"])
    history["temperature"] = history["temperature"][-30:]

    history["vibration"].append(state["vibration"])
    history["vibration"] = history["vibration"][-30:]

    history["load"].append(state["load"])
    history["load"] = history["load"][-30:]


def advance(hours=1):
    state["hours"] += hours
    state["cycles"] += hours * 2

    noise = lambda: random.random() - 0.35

    state["temperature"] = clamp(
        state["temperature"] + 0.055 * hours * 0.8 + noise() * 0.65,
        64,
        105,
    )

    state["vibration"] = clamp(
        state["vibration"] + 0.055 * hours * 0.055 + noise() * 0.12,
        2,
        7.8,
    )

    state["pressure"] = clamp(
        state["pressure"] - 0.055 * hours * 0.012 + noise() * 0.018,
        2.7,
        5.1,
    )

    state["load"] = clamp(
        state["load"] + noise() * 2.2,
        48,
        94,
    )

    wear = (
        max(0, state["temperature"] - 70) * 0.018
        + max(0, state["vibration"] - 3) * 0.9
        + max(0, 4.5 - state["pressure"]) * 1.2
    )

    state["health"] = clamp(
        91 - state["hours"] * 0.055 - wear,
        18,
        91,
    )

    state["rul"] = clamp(
        486 - state["hours"] * 1.3 - wear * 8,
        24,
        486,
    )

    state["failure"] = clamp(
        4.8 + (91 - state["health"]) * 1.45 + wear * 2.4,
        1,
        96,
    )

    add_history()


def recommendations():
    result = []

    if state["vibration"] > 5.5:
        result.append({
            "icon": "◉",
            "title": "Немедленно проверить подшипник",
            "text": f'Вибрация {state["vibration"]:.1f} mm/s. Возможен износ роликов.',
            "level": "high",
            "label": "срочно",
        })
        result.append({
            "icon": "⚙",
            "title": "Проверить соосность вала",
            "text": "Возможен перекос приводного вала или ослабление креплений.",
            "level": "high",
            "label": "срочно",
        })
        result.append({
            "icon": "🔧",
            "title": "Проверить крепление корпуса",
            "text": "Ослабленные крепления могут усиливать вибрацию станка.",
            "level": "medium",
            "label": "проверить",
        })
    elif state["vibration"] > 3.8:
        result.append({
            "icon": "◉",
            "title": "Запланировать диагностику подшипника",
            "text": f'Вибрация выросла до {state["vibration"]:.1f} mm/s.',
            "level": "medium",
            "label": "скоро",
        })
    else:
        result.append({
            "icon": "◉",
            "title": "Подшипник работает штатно",
            "text": "Вибрация находится в допустимом диапазоне.",
            "level": "low",
            "label": "норма",
        })

    if state["temperature"] > 88:
        result.append({
            "icon": "♨",
            "title": "Остановить станок из-за перегрева",
            "text": f'Температура двигателя {state["temperature"]:.1f} °C.',
            "level": "high",
            "label": "срочно",
        })
        result.append({
            "icon": "❄",
            "title": "Проверить систему охлаждения",
            "text": "Очистить радиатор и проверить работу вентилятора.",
            "level": "high",
            "label": "срочно",
        })
    elif state["temperature"] > 76:
        result.append({
            "icon": "♨",
            "title": "Проверить вентиляцию двигателя",
            "text": f'Температура повышена: {state["temperature"]:.1f} °C.',
            "level": "medium",
            "label": "скоро",
        })
    else:
        result.append({
            "icon": "♨",
            "title": "Температурный режим стабильный",
            "text": f'Текущая температура {state["temperature"]:.1f} °C.',
            "level": "low",
            "label": "норма",
        })

    if state["pressure"] < 3.6:
        result.append({
            "icon": "↘",
            "title": "Заменить масло и проверить насос",
            "text": f'Давление масла упало до {state["pressure"]:.1f} bar.',
            "level": "high",
            "label": "срочно",
        })
        result.append({
            "icon": "!",
            "title": "Проверить утечку масла",
            "text": "Низкое давление может быть связано с утечкой.",
            "level": "high",
            "label": "срочно",
        })
        result.append({
            "icon": "▣",
            "title": "Заменить масляный фильтр",
            "text": "Загрязненный фильтр может снижать давление.",
            "level": "medium",
            "label": "обслужить",
        })
    elif state["pressure"] < 4.3:
        result.append({
            "icon": "↘",
            "title": "Проверить уровень масла",
            "text": f'Давление масла снижается: {state["pressure"]:.1f} bar.',
            "level": "medium",
            "label": "скоро",
        })

    if state["load"] > 82:
        result.append({
            "icon": "⚡",
            "title": "Снизить нагрузку на привод",
            "text": f'Нагрузка достигла {state["load"]:.0f}%.',
            "level": "high",
            "label": "срочно",
        })
        result.append({
            "icon": "↻",
            "title": "Проверить ремень и муфту",
            "text": "Высокая нагрузка может вызвать проскальзывание.",
            "level": "medium",
            "label": "проверить",
        })
        result.append({
            "icon": "⚙",
            "title": "Проверить редуктор",
            "text": "Осмотри зубчатые передачи и уровень смазки.",
            "level": "medium",
            "label": "проверить",
        })

    if state["health"] < 70:
        result.append({
            "icon": "🧰",
            "title": "Запланировать техническое обслуживание",
            "text": f'Индекс здоровья: {state["health"]:.0f}%.',
            "level": "medium",
            "label": "обслужить",
        })
        result.append({
            "icon": "📋",
            "title": "Создать заявку на ремонт",
            "text": "Рекомендуется назначить инженера для диагностики.",
            "level": "medium",
            "label": "заявка",
        })

    if state["rul"] < 120:
        result.append({
            "icon": "⏱",
            "title": "Подготовить запасные детали",
            "text": f'Остаточный ресурс: {state["rul"]:.0f} часов.',
            "level": "high",
            "label": "подготовить",
        })

    if state["failure"] > 35:
        result.append({
            "icon": "⛔",
            "title": "Остановить оборудование",
            "text": "Вероятность отказа стала критической.",
            "level": "high",
            "label": "стоп",
        })

    return result[:10]


def get_payload():
    return {
        "state": state,
        "history": history,
        "recommendations": recommendations(),
    }


HTML = r"""
<!doctype html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ПобедИИтели</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
:root {
  --bg: #eef5f7;
  --card: #fff;
  --border: #dce9ed;
  --text: #17323d;
  --muted: #728992;
  --teal: #238f99;
  --green: #29986e;
  --yellow: #c48c26;
  --red: #d95763;
  --shadow: 0 14px 35px rgba(43,87,103,.11);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  color: var(--text);
  background:
    radial-gradient(circle at 0 0, rgba(111,190,201,.23), transparent 27%),
    radial-gradient(circle at 100% 5%, rgba(127,171,225,.2), transparent 30%),
    linear-gradient(135deg,#edf6f8,#f9fbfc 52%,#edf4f7);
  font-family: Arial, sans-serif;
}
.app { width:min(1480px,calc(100% - 40px)); margin:auto; padding:26px 0 40px; }
header { display:flex; justify-content:space-between; gap:24px; margin-bottom:24px; }
.brand { display:flex; align-items:center; gap:14px; }
.logo { display:grid; place-items:center; width:54px; height:54px; border-radius:16px; color:white; background:linear-gradient(145deg,#197c88,#43a8a9); font-weight:bold; }
.eyebrow { margin-bottom:8px; color:#176b76; font-size:10px; font-weight:bold; letter-spacing:.2em; text-transform:uppercase; }
h1 { margin:0; font-size:clamp(30px,4vw,46px); letter-spacing:-.06em; }
.subtitle { max-width:700px; margin:13px 0 0; color:var(--muted); font-size:14px; line-height:1.55; }
.actions { display:flex; justify-content:flex-end; align-items:center; gap:8px; flex-wrap:wrap; }
button,select { border:1px solid var(--border); border-radius:11px; color:var(--text); background:white; font:inherit; cursor:pointer; }
button { padding:11px 15px; transition:.2s; }
button:hover { transform:translateY(-1px); border-color:var(--teal); }
button.primary { color:white; border:0; background:linear-gradient(135deg,#197d88,#309fa0); font-weight:bold; }
button.danger { color:#b64f5a; border-color:#f0c8cc; background:#fff8f8; }
select { padding:10px 12px; }
.status { display:inline-flex; align-items:center; gap:8px; padding:9px 12px; border:1px solid #cbe8d8; border-radius:999px; color:var(--green); background:#f0fbf4; font-size:12px; font-weight:bold; white-space:nowrap; }
.dot { width:8px; height:8px; border-radius:50%; background:currentColor; box-shadow:0 0 10px currentColor; }
.grid { display:grid; gap:16px; }
.metrics { grid-template-columns:repeat(4,1fr); margin-bottom:16px; }
.main { grid-template-columns:1fr 1.45fr; }
.bottom { grid-template-columns:1.1fr .9fr; margin-top:16px; }
.panel { overflow:hidden; border:1px solid var(--border); border-radius:20px; background:rgba(255,255,255,.9); box-shadow:var(--shadow); }
.metric { min-height:145px; padding:20px; }
.metric-title { color:var(--muted); font-size:12px; font-weight:bold; letter-spacing:.08em; text-transform:uppercase; }
.metric-value { margin-top:18px; font-size:clamp(28px,4vw,42px); font-weight:900; letter-spacing:-.06em; }
.metric-info { display:flex; justify-content:space-between; gap:8px; margin-top:10px; color:var(--muted); font-size:12px; }
.positive { color:var(--green); }
.warning { color:var(--yellow); }
.critical { color:var(--red); }
.panel-inner,.health,.time-panel { padding:20px; }
.panel-head { display:flex; justify-content:space-between; align-items:center; gap:14px; margin-bottom:16px; }
.panel-title { font-size:17px; font-weight:800; }
.panel-description { margin-top:5px; color:var(--muted); font-size:12px; line-height:1.4; }
.recommendations { display:grid; gap:10px; max-height:425px; overflow-y:auto; }
.recommendation { display:grid; grid-template-columns:42px 1fr auto; align-items:center; gap:12px; padding:13px; border:1px solid #e0ebef; border-radius:14px; background:#f9fcfd; }
.rec-icon { display:grid; place-items:center; width:42px; height:42px; border-radius:13px; color:#a8771d; background:#fff5d9; font-size:18px; }
.recommendation strong { display:block; margin-bottom:4px; font-size:13px; }
.recommendation small { color:var(--muted); font-size:11px; line-height:1.4; }
.tag { padding:5px 8px; border-radius:999px; font-size:10px; font-weight:bold; text-transform:uppercase; white-space:nowrap; }
.tag.low { color:var(--green); background:#eaf8f0; }
.tag.medium { color:var(--yellow); background:#fff6dc; }
.tag.high { color:var(--red); background:#fff0f1; }
.chart-box { height:352px; }
.ring { display:grid; place-items:center; position:relative; width:185px; height:185px; margin:22px auto 18px; border-radius:50%; background:conic-gradient(var(--teal) 0deg,var(--teal) 327deg,#e5eef0 327deg); }
.ring:before { content:""; position:absolute; inset:12px; border-radius:50%; background:white; }
.ring-content { position:relative; text-align:center; }
.health-number { display:block; font-size:48px; font-weight:900; }
.health-label { color:var(--muted); font-size:11px; text-transform:uppercase; }
.details { display:grid; gap:9px; }
.detail { display:flex; justify-content:space-between; padding:11px 0; border-bottom:1px solid #e7eef1; font-size:13px; }
.detail span { color:var(--muted); }
.machine { display:flex; align-items:center; gap:14px; margin-top:18px; padding:14px; border:1px solid #cfe7e8; border-radius:15px; background:#effafa; }
.machine-image { width:78px; height:59px; border:2px solid #75aeb5; border-radius:8px; background:linear-gradient(145deg,#d8edef,#fff); }
.machine-info strong { display:block; margin-bottom:5px; font-size:14px; }
.machine-info span { color:var(--muted); font-size:12px; }
.sensors { grid-template-columns:repeat(2,1fr); }
.sensor { padding:16px; border:1px solid #e0ebef; border-radius:15px; background:#f9fcfd; }
.sensor-top { display:flex; justify-content:space-between; color:var(--muted); font-size:12px; }
.sensor-value { margin:11px 0 12px; font-size:25px; font-weight:900; }
.bar { height:6px; overflow:hidden; border-radius:99px; background:#e5eef0; }
.bar i { display:block; width:50%; height:100%; border-radius:inherit; background:var(--teal); transition:.4s; }
.time-panel { margin-top:16px; }
.time-buttons,.scenario { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.time-buttons button,.scenario button { padding:9px 11px; font-size:12px; }
.time-value { margin-left:auto; color:var(--muted); font-size:13px; }
.time-value strong { color:#176b76; font-size:17px; }
.scenario { margin-top:12px; }
.footer { margin-top:18px; color:var(--muted); font-size:11px; text-align:right; }
@media(max-width:1100px) {
  .metrics,.main,.bottom { grid-template-columns:repeat(2,1fr); }
}
@media(max-width:700px) {
  .app { width:calc(100% - 24px); }
  header { display:block; }
  .actions { justify-content:flex-start; margin-top:18px; }
  .metrics,.main,.bottom,.sensors { grid-template-columns:1fr; }
  .chart-box { height:270px; }
  .time-value { width:100%; margin-left:0; }
  .recommendation { grid-template-columns:38px 1fr; }
  .tag { grid-column:2; justify-self:start; }
}
</style>
</head>

<body>
<main class="app">
<header>
  <div>
    <div class="brand">
      <div class="logo">ИИ</div>
      <div>
        <div class="eyebrow">Команда разработчиков</div>
        <h1>ПобедИИтели</h1>
      </div>
    </div>
    <p class="subtitle">
      ИИ-система прогнозирования остаточного ресурса промышленного оборудования
      по данным телеметрии.
    </p>
  </div>

  <div class="actions">
    <span class="status" id="status"><i class="dot"></i> Система готова</span>
    <select id="speed">
      <option value="1">Скорость x1</option>
      <option value="2">Скорость x2</option>
      <option value="4">Скорость x4</option>
      <option value="8">Скорость x8</option>
    </select>
    <button class="primary" id="startButton">▶ Запустить</button>
    <button class="danger" id="resetButton">↺ Сбросить</button>
  </div>
</header>

<section class="grid metrics">
  <article class="panel metric">
    <div class="metric-title">Остаточный ресурс</div>
    <div class="metric-value" id="rul">486 ч</div>
    <div class="metric-info"><span>Прогноз ИИ</span><strong class="positive" id="rulState">стабильно</strong></div>
  </article>
  <article class="panel metric">
    <div class="metric-title">Вероятность отказа</div>
    <div class="metric-value" id="failure">4.8%</div>
    <div class="metric-info"><span>Горизонт 30 дней</span><strong class="positive" id="risk">низкий риск</strong></div>
  </article>
  <article class="panel metric">
    <div class="metric-title">Циклы работы</div>
    <div class="metric-value" id="cycles">12 840</div>
    <div class="metric-info"><span>Общая наработка</span><strong id="cycleSpeed">+0 / мин</strong></div>
  </article>
  <article class="panel metric">
    <div class="metric-title">Точность ИИ</div>
    <div class="metric-value">98.2%</div>
    <div class="metric-info"><span>Прогноз модели</span><strong class="positive">online</strong></div>
  </article>
</section>

<section class="grid main">
  <article class="panel">
    <div class="panel-inner">
      <div class="panel-head">
        <div>
          <div class="panel-title">Рекомендации ИИ</div>
          <div class="panel-description">Что проверить, заменить или обслужить</div>
        </div>
        <span class="status"><i class="dot"></i> Анализ</span>
      </div>
      <div class="recommendations" id="recommendations"></div>
    </div>
  </article>

  <article class="panel">
    <div class="panel-inner">
      <div class="panel-head">
        <div>
          <div class="panel-title">Телеметрия оборудования</div>
          <div class="panel-description">Температура, вибрация и нагрузка</div>
        </div>
        <span class="status"><i class="dot"></i> Live</span>
      </div>
      <div class="chart-box">
        <canvas id="chart"></canvas>
      </div>
    </div>
  </article>
</section>

<section class="grid bottom">
  <article class="panel health">
    <div class="panel-head">
      <div>
        <div class="panel-title">Состояние станка</div>
        <div class="panel-description">Комплексная оценка исправности</div>
      </div>
    </div>

    <div class="ring" id="ring">
      <div class="ring-content">
        <span class="health-number" id="health">91</span>
        <span class="health-label">здоровье</span>
      </div>
    </div>

    <div class="details">
      <div class="detail"><span>Статус</span><strong id="healthStatus" class="positive">Норма</strong></div>
      <div class="detail"><span>Уверенность ИИ</span><strong>94.6%</strong></div>
      <div class="detail"><span>Обновлено</span><strong id="updated">только что</strong></div>
    </div>

    <div class="machine">
      <div class="machine-image"></div>
      <div class="machine-info">
        <strong>Токарный станок CNC-04</strong>
        <span id="machineText">Работает в штатном режиме</span>
      </div>
    </div>
  </article>

  <article class="panel">
    <div class="panel-inner">
      <div class="panel-head">
        <div>
          <div class="panel-title">Показатели датчиков</div>
          <div class="panel-description">Текущие значения телеметрии</div>
        </div>
      </div>

      <div class="grid sensors">
        <div class="sensor">
          <div class="sensor-top"><span>Температура</span><span>°C</span></div>
          <div class="sensor-value" id="temperature">68.4</div>
          <div class="bar"><i id="temperatureBar"></i></div>
        </div>
        <div class="sensor">
          <div class="sensor-top"><span>Вибрация</span><span>mm/s</span></div>
          <div class="sensor-value" id="vibration">2.8</div>
          <div class="bar"><i id="vibrationBar"></i></div>
        </div>
        <div class="sensor">
          <div class="sensor-top"><span>Давление масла</span><span>bar</span></div>
          <div class="sensor-value" id="pressure">4.9</div>
          <div class="bar"><i id="pressureBar"></i></div>
        </div>
        <div class="sensor">
          <div class="sensor-top"><span>Нагрузка</span><span>%</span></div>
          <div class="sensor-value" id="load">61</div>
          <div class="bar"><i id="loadBar"></i></div>
        </div>
      </div>
    </div>
  </article>
</section>

<section class="panel time-panel">
  <div class="panel-head">
    <div>
      <div class="panel-title">Управление временем симуляции</div>
      <div class="panel-description">Накручивай часы и показывай износ оборудования</div>
    </div>
  </div>

  <div class="time-buttons">
    <button onclick="changeTime(1)">+1 час</button>
    <button onclick="changeTime(10)">+10 часов</button>
    <button onclick="changeTime(50)">+50 часов</button>
    <button onclick="changeTime(100)">+100 часов</button>
    <button onclick="changeTime(250)">+250 часов</button>
    <span class="time-value">Прошло: <strong id="time">0 ч</strong></span>
  </div>

  <div class="scenario">
    <button onclick="scenario('bearing')">Износ подшипника</button>
    <button onclick="scenario('heat')">Перегрев двигателя</button>
    <button onclick="scenario('oil')">Нехватка масла</button>
    <button onclick="scenario('critical')">Критический износ</button>
  </div>
</section>

<div class="footer">Демонстрационный проект · Команда «ПобедИИтели»</div>
</main>

<script>
let data = null;
let timer = null;

const chart = new Chart(document.getElementById("chart"), {
  type: "line",
  data: {
    labels: Array.from({ length: 30 }, (_, i) => `${30 - i} мин`),
    datasets: [
      {
        label: "Температура",
        data: [],
        borderColor: "#dc7a35",
        backgroundColor: "rgba(220,122,53,.10)",
        fill: true,
        tension: .38,
        pointRadius: 0,
        borderWidth: 2
      },
      {
        label: "Вибрация x10",
        data: [],
        borderColor: "#d95763",
        backgroundColor: "rgba(217,87,99,.05)",
        fill: true,
        tension: .38,
        pointRadius: 0,
        borderWidth: 2
      },
      {
        label: "Нагрузка",
        data: [],
        borderColor: "#238f99",
        backgroundColor: "rgba(35,143,153,.07)",
        fill: true,
        tension: .38,
        pointRadius: 0,
        borderWidth: 2
      }
    ]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      intersect: false,
      mode: "index"
    },
    plugins: {
      legend: {
        labels: {
          color: "#526f79",
          usePointStyle: true
        }
      }
    },
    scales: {
      x: {
        grid: { color: "rgba(40,90,100,.08)" },
        ticks: { color: "#789099" }
      },
      y: {
        min: 0,
        max: 110,
        grid: { color: "rgba(40,90,100,.08)" },
        ticks: { color: "#789099" }
      }
    }
  }
});

function render(payload) {
  data = payload;
  const s = data.state;

  document.getElementById("rul").textContent = `${Math.round(s.rul)} ч`;
  document.getElementById("failure").textContent = `${s.failure.toFixed(1)}%`;
  document.getElementById("cycles").textContent = Math.round(s.cycles).toLocaleString("ru-RU");
  document.getElementById("time").textContent = `${Math.round(s.hours)} ч`;

  document.getElementById("health").textContent = Math.round(s.health);

  const degree = s.health * 3.6;
  const color = s.health < 45 ? "#d95763" : s.health < 70 ? "#c48c26" : "#238f99";

  document.getElementById("ring").style.background =
    `conic-gradient(${color} 0deg, ${color} ${degree}deg, #e5eef0 ${degree}deg)`;

  const healthStatus = document.getElementById("healthStatus");
  healthStatus.textContent = s.health < 45 ? "Критично" : s.health < 70 ? "Предупреждение" : "Норма";
  healthStatus.className = s.health < 45 ? "critical" : s.health < 70 ? "warning" : "positive";

  const risk = document.getElementById("risk");
  risk.textContent = s.failure >= 35 ? "критический риск" : s.failure >= 15 ? "повышенный риск" : "низкий риск";
  risk.className = s.failure >= 35 ? "critical" : s.failure >= 15 ? "warning" : "positive";

  const rulState = document.getElementById("rulState");
  rulState.textContent = s.rul < 180 ? "снижается" : s.rul < 320 ? "под наблюдением" : "стабильно";
  rulState.className = s.rul < 180 ? "critical" : s.rul < 320 ? "warning" : "positive";

  document.getElementById("temperature").textContent = s.temperature.toFixed(1);
  document.getElementById("vibration").textContent = s.vibration.toFixed(1);
  document.getElementById("pressure").textContent = s.pressure.toFixed(1);
  document.getElementById("load").textContent = Math.round(s.load);

  setBar("temperatureBar", s.temperature, 110);
  setBar("vibrationBar", s.vibration, 8);
  setBar("pressureBar", 7 - s.pressure, 4);
  setBar("loadBar", s.load, 100);

  document.getElementById("machineText").textContent =
    s.health < 45
      ? "Требуется остановка и срочный ремонт"
      : s.health < 70
        ? "Работа разрешена, нужна диагностика"
        : "Работает в штатном режиме";

  document.getElementById("recommendations").innerHTML =
    data.recommendations.map((item) => `
      <div class="recommendation">
        <div class="rec-icon">${item.icon}</div>
        <div>
          <strong>${item.title}</strong>
          <small>${item.text}</small>
        </div>
        <span class="tag ${item.level}">${item.label}</span>
      </div>
    `).join("");

  chart.data.datasets[0].data = data.history.temperature;
  chart.data.datasets[1].data = data.history.vibration.map(x => x * 10);
  chart.data.datasets[2].data = data.history.load;
  chart.update("none");
}

function setBar(id, value, max) {
  const percent = Math.max(5, Math.min(100, value / max * 100));
  const element = document.getElementById(id);
  element.style.width = `${percent}%`;
  element.style.background =
    percent > 82 ? "#d95763" : percent > 62 ? "#c48c26" : "#238f99";
}

async function update(url) {
  const response = await fetch(url);
  const payload = await response.json();
  render(payload);
}

async function toggleSimulation() {
  await update("/api/toggle");
  const button = document.getElementById("startButton");

  if (data.state.running) {
    button.textContent = "Ⅱ Пауза";
    document.getElementById("status").innerHTML = '<i class="dot"></i> Симуляция активна';
    timer = setInterval(() => update("/api/tick"), 1000);
  } else {
    button.textContent = "▶ Запустить";
    document.getElementById("status").innerHTML = '<i class="dot"></i> Симуляция на паузе';
    clearInterval(timer);
  }
}

async function changeTime(hours) {
  clearInterval(timer);
  await update(`/api/time/${hours}`);
  document.getElementById("status").innerHTML = '<i class="dot"></i> Время прокручено вручную';
}

async function scenario(type) {
  clearInterval(timer);
  await update(`/api/scenario/${type}`);
  document.getElementById("startButton").textContent = "▶ Запустить";
  document.getElementById("status").innerHTML = '<i class="dot"></i> Загружен сценарий';
}

document.getElementById("startButton").addEventListener("click", toggleSimulation);
document.getElementById("resetButton").addEventListener("click", () => update("/api/reset"));

update("/api/state");
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/state")
def api_state():
    return jsonify(get_payload())


@app.route("/api/tick")
def api_tick():
    if state["running"]:
        advance(1)
    return jsonify(get_payload())


@app.route("/api/toggle")
def api_toggle():
    state["running"] = not state["running"]
    return jsonify(get_payload())


@app.route("/api/reset")
def api_reset():
    state.update(initial)
    state["running"] = False

    history["temperature"] = [64 + random.random() * 7 for _ in range(30)]
    history["vibration"] = [2 + random.random() * 0.8 for _ in range(30)]
    history["load"] = [55 + random.random() * 12 for _ in range(30)]

    return jsonify(get_payload())


@app.route("/api/time/<int:hours>")
def api_time(hours):
    state["running"] = False

    for _ in range(max(1, min(hours, 500))):
        advance(1)

    return jsonify(get_payload())


@app.route("/api/scenario/<name>")
def api_scenario(name):
    state["running"] = False

    if name == "bearing":
        state["vibration"] = 6.6
        state["load"] = 84
        state["health"] = 52
        state["rul"] = 130
        state["failure"] = 42

    elif name == "heat":
        state["temperature"] = 96
        state["load"] = 88
        state["health"] = 45
        state["rul"] = 94
        state["failure"] = 58

    elif name == "oil":
        state["pressure"] = 3.1
        state["temperature"] = 84
        state["health"] = 48
        state["rul"] = 105
        state["failure"] = 51

    elif name == "critical":
        state["temperature"] = 101
        state["vibration"] = 7.3
        state["pressure"] = 2.9
        state["load"] = 93
        state["health"] = 23
        state["rul"] = 28
        state["failure"] = 91

    add_history()
    return jsonify(get_payload())


if __name__ == "__main__":
    print("Сайт запущен: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
