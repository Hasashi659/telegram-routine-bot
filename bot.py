"""
Bot de Telegram para notificaciones de rutina
Desplegar en Render.com para 24/7
"""

import os
import time
import logging
from datetime import datetime, timezone, timedelta
import requests
from flask import Flask, jsonify, request

# Zona horaria de Colombia (UTC-5)
TZ_COLOMBIA = timezone(timedelta(hours=-5))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURACIÓN
# ============================================

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8872994414:AAFBL1OFjUSOSmEcZHwKjeXWllvztHZUZUI')
OWNER_CHAT_ID = os.environ.get('CHAT_ID', '6613206978')  # Solo este ID puede usar el bot

# ============================================
# HORARIO DE LA RUTINA
# ============================================

ROUTINE = [
    {"time": "05:30", "task": "Despertar sin celular", "emoji": "🧠"},
    {"time": "05:45", "task": "Meditación", "emoji": "🧠"},
    {"time": "06:00", "task": "Journaling", "emoji": "🧠"},
    {"time": "06:15", "task": "Visualización", "emoji": "🧠"},
    {"time": "06:30", "task": "Ejercicio", "emoji": "💪"},
    {"time": "07:15", "task": "Ducharse", "emoji": "🚿"},
    {"time": "07:30", "task": "Desayuno + Inglés", "emoji": "📚"},
    {"time": "08:00", "task": "Trabajo / Estudio", "emoji": "💼"},
    {"time": "12:00", "task": "Almuerzo", "emoji": "☕"},
    {"time": "13:00", "task": "Vibecoding Block 1", "emoji": "💻"},
    {"time": "15:00", "task": "Break", "emoji": "☕"},
    {"time": "15:15", "task": "Vibecoding Block 2", "emoji": "💻"},
    {"time": "17:15", "task": "Break", "emoji": "☕"},
    {"time": "17:30", "task": "Vibecoding Block 3", "emoji": "💻"},
    {"time": "19:00", "task": "Matemáticas", "emoji": "📐"},
    {"time": "19:30", "task": "Inglés", "emoji": "🇬🇧"},
    {"time": "20:00", "task": "Finanzas", "emoji": "💰"},
    {"time": "20:30", "task": "Trading", "emoji": "📈"},
    {"time": "21:00", "task": "Lectura", "emoji": "📖"},
    {"time": "21:30", "task": "Videos + Reflexión", "emoji": "🎬"},
    {"time": "21:45", "task": "Sin pantallas", "emoji": "🌙"},
    {"time": "22:00", "task": "Dormir", "emoji": "😴"},
]

# ============================================
# FUNCIONES DE TELEGRAM
# ============================================

def send_message(text):
    """Enviar mensaje SOLO al dueño"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": OWNER_CHAT_ID,  # Solo envía al dueño
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result.get("ok"):
            logger.info(f"Mensaje enviado al dueño: {text[:50]}...")
            return True
        else:
            logger.error(f"Error Telegram: {result.get('description')}")
            return False
    except Exception as e:
        logger.error(f"Error enviando: {e}")
        return False

def is_owner(update):
    """Verificar si el mensaje es del dueño"""
    if update.get("message"):
        chat_id = str(update["message"]["chat"]["id"])
        return chat_id == OWNER_CHAT_ID
    return False

def get_current_time():
    """Obtener hora actual en Colombia"""
    return datetime.now(TZ_COLOMBIA)

def get_current_task():
    """Obtener tarea actual"""
    current_time = get_current_time().strftime("%H:%M")
    for i in range(len(ROUTINE) - 1, -1, -1):
        if current_time >= ROUTINE[i]["time"]:
            return ROUTINE[i]
    return ROUTINE[0]

def get_next_task():
    """Obtener siguiente tarea"""
    current_time = get_current_time().strftime("%H:%M")
    for task in ROUTINE:
        if current_time < task["time"]:
            return task
    return ROUTINE[0]

def get_minutes_until_next():
    """Minutos hasta siguiente tarea"""
    current_time = get_current_time().strftime("%H:%M")
    for task in ROUTINE:
        if current_time < task["time"]:
            now = get_current_time()
            task_time = datetime.strptime(task["time"], "%H:%M").replace(
                year=now.year, month=now.month, day=now.day,
                tzinfo=TZ_COLOMBIA
            )
            diff = task_time - now
            return max(0, int(diff.total_seconds() / 60))
    return 0

def get_progress():
    """Progreso del día"""
    current_time = get_current_time().strftime("%H:%M")
    completed = sum(1 for t in ROUTINE if current_time >= t["time"])
    return int((completed / len(ROUTINE)) * 100)

# ============================================
# SERVIDOR WEB
# ============================================

app = Flask(__name__)

@app.route('/')
def home():
    """Endpoint principal - verifica que el bot esté vivo y envía notificación"""
    current = get_current_task()
    next_task = get_next_task()
    minutes = get_minutes_until_next()
    progress = get_progress()
    
    # Siempre enviar notificación de tarea actual
    msg = f"""🔔 <b>TAREA ACTUAL</b>

<b>Ahora:</b> {current['emoji']} {current['task']}
<b>Próxima:</b> {next_task['task']} (en {minutes} min)
📊 Progreso: {progress}%"""
    
    send_message(msg)
    
    return jsonify({
        "status": "running",
        "current_task": current["task"],
        "next_task": next_task["task"],
        "minutes_until_next": minutes,
        "progress": f"{progress}%",
        "time": get_current_time().isoformat(),
        "timezone": "America/Bogota (UTC-5)"
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/test')
def test():
    """Endpoint de prueba"""
    send_message("🤖 Test desde Render.com!")
    return jsonify({"status": "test sent"})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook para recibir mensajes - SOLO procesa del dueño"""
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "no data"})
    
    # Verificar si es del dueño
    if not is_owner(data):
        logger.warning(f"Mensaje bloqueado de usuario no autorizado: {data}")
        return jsonify({"status": "blocked"})
    
    # Procesar comando del dueño
    if data.get("message", {}).get("text"):
        text = data["message"]["text"]
        
        if text == "/status":
            current = get_current_task()
            next_task = get_next_task()
            minutes = get_minutes_until_next()
            progress = get_progress()
            
            msg = f"""📊 <b>ESTADO DEL BOT</b>

<b>Tarea actual:</b> {current['emoji']} {current['task']}
<b>Próxima:</b> {next_task['task']} ({minutes} min)
<b>Progreso:</b> {progress}%
<b>Hora Colombia:</b> {get_current_time().strftime('%H:%M')}
<b>Estado:</b> ✅ Activo 24/7"""
            
            send_message(msg)
        
        elif text == "/test":
            send_message("✅ Bot funcionando correctamente!")
    
    return jsonify({"status": "ok"})

# ============================================
# LÓGICA DE NOTIFICACIONES
# ============================================

last_notified_task = ""

def check_and_notify():
    """Verificar y enviar notificaciones"""
    global last_notified_task
    
    current = get_current_task()
    current_time = get_current_time().strftime("%H:%M")
    
    # Notificar cambio de tarea
    if current["task"] != last_notified_task:
        next_task = get_next_task()
        minutes = get_minutes_until_next()
        progress = get_progress()
        
        msg = f"""🔔 <b>CAMBIO DE TAREA</b>

<b>Ahora:</b> {current['emoji']} {current['task']}
<b>Próxima:</b> {next_task['task']} (en {minutes} min)
📊 Progreso: {progress}%"""
        
        send_message(msg)
        last_notified_task = current["task"]
        logger.info(f"Tarea cambiada: {current['task']}")
    
    # Recordatorio 5 min antes
    minutes = get_minutes_until_next()
    if minutes == 5:
        next_task = get_next_task()
        send_message(f"⏰ <b>5 minutos</b> - Prepárate para: {next_task['emoji']} {next_task['task']}")
    
    # Buenos días (05:30)
    if current_time == "05:30":
        date = datetime.now().strftime("%A %d de %B")
        send_message(f"🌅 <b>¡Buenos días!</b>\n\n{date}\n\n¡Que tengas un día productivo!")
    
    # Buenas noches (22:00)
    if current_time == "22:00":
        progress = get_progress()
        send_message(f"🌙 <b>Buenas noches</b>\n\nProgreso de hoy: {progress}%\n\nDescansa bien!")

# ============================================
# MAIN
# ============================================

def setup_webhook():
    """Configurar webhook para recibir mensajes"""
    render_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://telegram-routine-bot.onrender.com')
    webhook_url = f"{render_url}/webhook"
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    data = {"url": webhook_url}
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result.get("ok"):
            logger.info(f"Webhook configurado: {webhook_url}")
        else:
            logger.error(f"Error webhook: {result.get('description')}")
    except Exception as e:
        logger.error(f"Error configurando webhook: {e}")

if __name__ == '__main__':
    logger.info("Iniciando bot...")
    
    # Configurar webhook
    setup_webhook()
    
    # Mensaje de inicio SOLO al dueño
    send_message("🤖 <b>Bot 24/7 ONLINE</b>\n\nEl notificador está activo y SEGURO.\nSolo tú puedes recibir notificaciones.\n\nComandos: /status, /test")
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
