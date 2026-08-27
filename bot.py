"""
Bot de Telegram para notificaciones de rutina
Desplegar en Render.com para 24/7
"""

import os
import time
import logging
from datetime import datetime, timedelta
import requests
from flask import Flask, jsonify

# ============================================
# CONFIGURACIÓN
# ============================================

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8872994414:AAFBL1OFjUSOSmEcZHwKjeXWllvztHZUZUI')
CHAT_ID = os.environ.get('CHAT_ID', '6613206978')

# ============================================
# HORARIO DE LA RUTINA
# ============================================

ROUTINE = [
    # Mañana
    {"time": "05:30", "task": "Despertar sin celular", "category": "salud-mental", "duration": 15, "emoji": "🧠"},
    {"time": "05:45", "task": "Meditación", "category": "salud-mental", "duration": 15, "emoji": "🧠"},
    {"time": "06:00", "task": "Journaling: 3 gratitudes", "category": "salud-mental", "duration": 15, "emoji": "🧠"},
    {"time": "06:15", "task": "Visualización del día", "category": "salud-mental", "duration": 15, "emoji": "🧠"},
    {"time": "06:30", "task": "Ejercicio", "category": "salud-fisica", "duration": 45, "emoji": "💪"},
    {"time": "07:15", "task": "Ducharse + aseo", "category": "higiene", "duration": 15, "emoji": "🚿"},
    {"time": "07:30", "task": "Desayuno + Inglés", "category": "aprendizaje", "duration": 30, "emoji": "📚"},
    
    # Trabajo
    {"time": "08:00", "task": "Trabajo presencial / Estudio", "category": "productividad", "duration": 240, "emoji": "💼"},
    
    # Mediodía
    {"time": "12:00", "task": "Almuerzo + caminar", "category": "descanso", "duration": 60, "emoji": "☕"},
    
    # Tarde - Vibecoding
    {"time": "13:00", "task": "💻 Vibecoding Block 1", "category": "vibecoding", "duration": 120, "emoji": "💻"},
    {"time": "15:00", "task": "☕ Break 15min", "category": "descanso", "duration": 15, "emoji": "☕"},
    {"time": "15:15", "task": "💻 Vibecoding Block 2", "category": "vibecoding", "duration": 120, "emoji": "💻"},
    {"time": "17:15", "task": "☕ Break 15min", "category": "descanso", "duration": 15, "emoji": "☕"},
    {"time": "17:30", "task": "💻 Vibecoding Block 3", "category": "vibecoding", "duration": 90, "emoji": "💻"},
    
    # Noche - Aprendizaje
    {"time": "19:00", "task": "📐 Matemáticas", "category": "aprendizaje", "duration": 30, "emoji": "📐"},
    {"time": "19:30", "task": "🇬🇧 Inglés avanzado", "category": "aprendizaje", "duration": 30, "emoji": "🇬🇧"},
    {"time": "20:00", "task": "💰 Finanzas / Trading", "category": "aprendizaje", "duration": 30, "emoji": "💰"},
    {"time": "20:30", "task": "📈 Trading / Finanzas", "category": "aprendizaje", "duration": 30, "emoji": "📈"},
    {"time": "21:00", "task": "📖 Lectura técnica", "category": "aprendizaje", "duration": 30, "emoji": "📖"},
    {"time": "21:30", "task": "🎬 Videos + Reflexión", "category": "aprendizaje", "duration": 30, "emoji": "🎬"},
    {"time": "21:45", "task": "🌙 Sin pantallas", "category": "descanso", "duration": 15, "emoji": "🌙"},
    {"time": "22:00", "task": "😴 Dormir", "category": "descanso", "duration": 450, "emoji": "😴"},
]

# ============================================
# FUNCIONES DE TELEGRAM
# ============================================

def send_message(text, silent=False):
    """Enviar mensaje a Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_notification": silent
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json().get("ok", False)
    except Exception as e:
        logging.error(f"Error enviando mensaje: {e}")
        return False

def get_current_task():
    """Obtener tarea actual"""
    current_time = datetime.now().strftime("%H:%M")
    for i in range(len(ROUTINE) - 1, -1, -1):
        if current_time >= ROUTINE[i]["time"]:
            return ROUTINE[i]
    return ROUTINE[0]

def get_next_task():
    """Obtener siguiente tarea"""
    current_time = datetime.now().strftime("%H:%M")
    for task in ROUTINE:
        if current_time < task["time"]:
            return task
    return ROUTINE[0]

def get_minutes_until_next():
    """Minutos hasta la siguiente tarea"""
    current_time = datetime.now().strftime("%H:%M")
    for task in ROUTINE:
        if current_time < task["time"]:
            now = datetime.now()
            task_time = datetime.strptime(task["time"], "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            diff = task_time - now
            return max(0, int(diff.total_seconds() / 60))
    return 0

def get_daily_progress():
    """Progreso del día"""
    current_time = datetime.now().strftime("%H:%M")
    completed = sum(1 for t in ROUTINE if current_time >= t["time"])
    return int((completed / len(ROUTINE)) * 100)

def get_progress_emoji(percent):
    """Emoji según progreso"""
    if percent >= 100: return "✅"
    if percent >= 75: return "🟢"
    if percent >= 50: return "🟡"
    if percent >= 25: return "🟠"
    return "🔴"

# ============================================
# MENSAJES
# ============================================

def format_task_change():
    """Mensaje de cambio de tarea"""
    current = get_current_task()
    next_task = get_next_task()
    minutes = get_minutes_until_next()
    progress = get_daily_progress()
    progress_emoji = get_progress_emoji(progress)
    
    return f"""<b>🔔 CAMBIO DE TAREA</b>

<b>Ahora:</b> {current['emoji']} {current['task']}
<b>Duración:</b> {current['duration']} min
<b>Categoría:</b> {current['category']}

<b>Próxima:</b> {next_task['task']} (en {minutes} min)

{progress_emoji} Progreso diario: {progress}%"""

def format_reminder(minutes):
    """Mensaje de recordatorio"""
    next_task = get_next_task()
    return f"""<b>⏰ RECORDATORIO - {minutes} min</b>

Prepárate para:
<b>{next_task['emoji']} {next_task['task']}</b>

Empieza en {minutes} minutos"""

def format_daily_summary():
    """Resumen del día"""
    progress = get_daily_progress()
    progress_emoji = get_progress_emoji(progress)
    current = get_current_task()
    next_task = get_next_task()
    minutes = get_minutes_until_next()
    
    return f"""<b>📊 RESUMEN DEL DÍA</b>

{progress_emoji} Progreso: {progress}%

<b>Tarea actual:</b> {current['emoji']} {current['task']}
<b>Próxima tarea:</b> {next_task['task']}
<b>Tiempo restante:</b> {minutes} min

<i>Buen trabajo manteniendo la rutina! 💪</i>"""

def format_morning():
    """Buenos días"""
    date = datetime.now().strftime("%A %d de %B")
    return f"""<b>🌅 ¡Buenos días!</b>

<b>{date}</b>

Hoy es un nuevo día para:
• 💻 Vibecoding: 5.5h
• 📚 Aprendizaje: 2.5h
• 💪 Ejercicio: 45min
• 📖 Lectura: 30min

<i>¡Que tengas un día productivo!</i>"""

def format_night():
    """Buenas noches"""
    progress = get_daily_progress()
    progress_emoji = get_progress_emoji(progress)
    return f"""<b>🌙 Buenas noches</b>

{progress_emoji} Progreso de hoy: {progress}%

<i>Descansa bien, mañana será otro día productivo.</i>

<b>Buenas noches! 😴</b>"""

# ============================================
# FLUJO PRINCIPAL
# ============================================

last_task = ""
last_date = ""

def check_and_send():
    """Verificar y enviar notificaciones"""
    global last_task, last_date
    
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    current_date = now.strftime("%Y-%m-%d")
    
    # Buenos días (05:30)
    if current_time == "05:30" and last_date != current_date:
        send_message(format_morning())
        last_date = current_date
    
    # Buenas noches (22:00)
    if current_time == "22:00":
        send_message(format_night())
    
    # Cambio de tarea
    current = get_current_task()
    if current["task"] != last_task:
        send_message(format_task_change())
        last_task = current["task"]
    
    # Recordatorio 5 min
    minutes = get_minutes_until_next()
    if minutes == 5:
        send_message(format_reminder(5), silent=True)
    
    # Recordatorio 1 min
    if minutes == 1:
        send_message(format_reminder(1))
    
    # Resumen cada 2 horas
    hour = now.hour
    if hour % 2 == 0 and now.minute == 0:
        send_message(format_daily_summary(), silent=True)

# ============================================
# SERVIDOR WEB (para Render)
# ============================================

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "bot": "Telegram Routine Notifier",
        "time": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Enviar mensaje de inicio
    send_message("<b>🤖 Bot 24/7 ONLINE</b>\n\nEl notificador está activo en la nube.\nFuncionará incluso cuando tu PC esté apagado.")
    
    logging.info("Bot iniciado")
    
    # Ejecutar verificación en background
    import threading
    
    def background_checker():
        while True:
            try:
                check_and_send()
            except Exception as e:
                logging.error(f"Error: {e}")
            time.sleep(30)
    
    checker_thread = threading.Thread(target=background_checker, daemon=True)
    checker_thread.start()
    
    # Servidor web (requerido por Render)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
