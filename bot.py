"""
Bot de Telegram para notificaciones de rutina
Desplegar en Render.com para 24/7
"""

import os
import json
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

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8866031857:AAFebwtF2BtmzQNYJQnT6t2r1ntqH38fhDo')
OWNER_CHAT_ID = os.environ.get('CHAT_ID', '6613206978')

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
# ESTADO DE NOTIFICACIONES
# ============================================

# Guardar qué notificaciones ya se enviaron hoy
notifications_sent = {
    "date": "",
    "warned": [],    # Tareas para las que se envió alerta de 5 min
    "started": [],   # Tareas que ya empezaron
    "morning": False,
    "night": False
}

def load_notifications():
    """Cargar estado de notificaciones"""
    global notifications_sent
    try:
        if os.path.exists('notifications_state.json'):
            with open('notifications_state.json', 'r') as f:
                data = json.load(f)
                # Solo cargar si es del mismo día
                if data.get("date") == get_current_time().strftime("%Y-%m-%d"):
                    notifications_sent = data
                    logger.info("Estado de notificaciones cargado")
    except Exception as e:
        logger.error(f"Error cargando estado: {e}")

def save_notifications():
    """Guardar estado de notificaciones"""
    try:
        notifications_sent["date"] = get_current_time().strftime("%Y-%m-%d")
        with open('notifications_state.json', 'w') as f:
            json.dump(notifications_sent, f)
    except Exception as e:
        logger.error(f"Error guardando estado: {e}")

def reset_daily():
    """Resetear notificaciones diarias"""
    global notifications_sent
    today = get_current_time().strftime("%Y-%m-%d")
    if notifications_sent["date"] != today:
        notifications_sent = {
            "date": today,
            "warned": [],
            "started": [],
            "morning": False,
            "night": False
        }
        logger.info(f"Notificaciones reseteadas para {today}")

# ============================================
# FUNCIONES DE TELEGRAM
# ============================================

def send_message(text):
    """Enviar mensaje SOLO al dueño"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": OWNER_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result.get("ok"):
            logger.info(f"Mensaje enviado: {text[:50]}...")
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

def get_current_time_str():
    """Hora actual como string HH:MM"""
    return get_current_time().strftime("%H:%M")

def get_current_task():
    """Obtener tarea actual"""
    current_time = get_current_time_str()
    for i in range(len(ROUTINE) - 1, -1, -1):
        if current_time >= ROUTINE[i]["time"]:
            return ROUTINE[i], i
    return ROUTINE[0], 0

def get_next_task():
    """Obtener siguiente tarea"""
    current_time = get_current_time_str()
    for i, task in enumerate(ROUTINE):
        if current_time < task["time"]:
            return task, i
    return ROUTINE[0], 0

def get_minutes_until(time_str):
    """Minutos hasta una hora específica"""
    now = get_current_time()
    task_time = datetime.strptime(time_str, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day,
        tzinfo=TZ_COLOMBIA
    )
    diff = task_time - now
    return int(diff.total_seconds() / 60)

def get_progress():
    """Progreso del día"""
    current_time = get_current_time_str()
    completed = sum(1 for t in ROUTINE if current_time >= t["time"])
    return int((completed / len(ROUTINE)) * 100)

# ============================================
# SISTEMA DE NOTIFICACIONES
# ============================================

def check_notifications():
    """Verificar y enviar notificaciones automáticas"""
    reset_daily()
    load_notifications()
    
    now = get_current_time_str()
    current_task, current_idx = get_current_task()
    next_task, next_idx = get_next_task()
    
    # ========================================
    # 1. NOTIFICACIÓN "5 MINUTOS ANTES"
    # ========================================
    if next_task:
        minutes_left = get_minutes_until(next_task["time"])
        
        # Alerta a los 5 minutos exactos
        if minutes_left == 5 and next_task["time"] not in notifications_sent["warned"]:
            msg = f"""⏰ <b>5 MINUTOS</b>

<b>Prepárate para:</b> {next_task['emoji']} {next_task['task']}
<b>Empieza a las:</b> {next_task['time']}

¡Quedan 5 minutos!"""
            
            send_message(msg)
            notifications_sent["warned"].append(next_task["time"])
            save_notifications()
            logger.info(f"Alerta 5 min enviada para {next_task['task']}")
        
        # Alerta a los 2 minutos (urgente)
        if minutes_left == 2 and f"{next_task['time']}_2min" not in notifications_sent["warned"]:
            msg = f"""🚨 <b>2 MINUTOS</b>

<b>Ya empieza:</b> {next_task['emoji']} {next_task['task']}
<b>A las:</b> {next_task['time']}

¡Prepárate ahora!"""
            
            send_message(msg)
            notifications_sent["warned"].append(f"{next_task['time']}_2min")
            save_notifications()
    
    # ========================================
    # 2. NOTIFICACIÓN "TAREA EMPEZÓ"
    # ========================================
    if current_task["time"] not in notifications_sent["started"]:
        progress = get_progress()
        
        msg = f"""🔔 <b>TAREA INICIADA</b>

<b>Ahora:</b> {current_task['emoji']} {current_task['task']}
<b>Horario:</b> {current_task['time']} - {next_task['time'] if next_task else 'Fin'}
📊 Progreso: {progress}%"""
        
        send_message(msg)
        notifications_sent["started"].append(current_task["time"])
        save_notifications()
        logger.info(f"Notificación tarea iniciada: {current_task['task']}")
    
    # ========================================
    # 3. BUENOS DÍAS (05:30)
    # ========================================
    if now >= "05:30" and now < "05:31" and not notifications_sent["morning"]:
        date = get_current_time().strftime("%A %d de %B")
        msg = f"""🌅 <b>¡BUENOS DÍAS!</b>

<b>Fecha:</b> {date}
<b>Hora:</b> {now}

<b>Rutina de hoy:</b>
🧠 05:30 - Despertar
💪 06:30 - Ejercicio
💼 08:00 - Trabajo
💻 13:00 - Vibecoding
📐 19:00 - Estudio

¡Que tengas un día productivo!"""
        
        send_message(msg)
        notifications_sent["morning"] = True
        save_notifications()
    
    # ========================================
    # 4. BUENAS NOCHES (22:00)
    # ========================================
    if now >= "22:00" and now < "22:01" and not notifications_sent["night"]:
        progress = get_progress()
        msg = f"""🌙 <b>BUENAS NOCHES</b>

<b>Progreso de hoy:</b> {progress}%
<b> hora:</b> {now}

Descansa bien. ¡Mañana un nuevo día!"""
        
        send_message(msg)
        notifications_sent["night"] = True
        save_notifications()

# ============================================
# SERVIDOR WEB
# ============================================

app = Flask(__name__)

@app.route('/')
def home():
    """Endpoint principal - verifica notificaciones"""
    check_notifications()
    
    current, _ = get_current_task()
    next_task, _ = get_next_task()
    minutes = get_minutes_until(next_task["time"]) if next_task else 0
    progress = get_progress()
    
    return jsonify({
        "status": "running",
        "current_task": current["task"],
        "next_task": next_task["task"] if next_task else "N/A",
        "minutes_until_next": minutes,
        "progress": f"{progress}%",
        "time": get_current_time().isoformat(),
        "timezone": "America/Bogota (UTC-5)"
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/check')
def check():
    """Endpoint para cron - solo verifica notificaciones"""
    check_notifications()
    return jsonify({
        "status": "checked",
        "time": get_current_time().isoformat()
    })

@app.route('/test')
def test():
    """Endpoint de prueba"""
    send_message("✅ Bot funcionando correctamente!")
    return jsonify({"status": "test sent"})

@app.route('/status')
def status():
    """Ver estado manual"""
    current, _ = get_current_task()
    next_task, _ = get_next_task()
    minutes = get_minutes_until(next_task["time"]) if next_task else 0
    progress = get_progress()
    
    msg = f"""📊 <b>ESTADO DEL BOT</b>

<b>Tarea actual:</b> {current['emoji']} {current['task']}
<b>Próxima:</b> {next_task['task'] if next_task else 'N/A'} ({minutes} min)
<b>Progreso:</b> {progress}%
<b>Hora:</b> {get_current_time().strftime('%H:%M')}"""
    
    send_message(msg)
    return jsonify({"status": "sent"})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook para recibir mensajes - SOLO procesa del dueño"""
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "no data"})
    
    if not is_owner(data):
        logger.warning(f"Mensaje bloqueado de usuario no autorizado")
        return jsonify({"status": "blocked"})
    
    if data.get("message", {}).get("text"):
        text = data["message"]["text"]
        
        if text == "/status":
            current, _ = get_current_task()
            next_task, _ = get_next_task()
            minutes = get_minutes_until(next_task["time"]) if next_task else 0
            progress = get_progress()
            
            msg = f"""📊 <b>ESTADO</b>

<b>Ahora:</b> {current['emoji']} {current['task']}
<b>Próxima:</b> {next_task['task'] if next_task else 'N/A'} ({minutes} min)
<b>Progreso:</b> {progress}%"""
            
            send_message(msg)
        
        elif text == "/test":
            send_message("✅ Bot funcionando!")
        
        elif text == "/help":
            msg = """📖 <b>COMANDOS</b>

/status - Ver estado actual
/test - Probar bot
/help - Ver esta ayuda"""
            send_message(msg)
    
    return jsonify({"status": "ok"})

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    logger.info("Iniciando bot...")
    
    # Cargar estado
    load_notifications()
    
    # Mensaje de inicio
    send_message("🤖 <b>Bot 24/7 ONLINE</b>\n\nNotificaciones automáticas activadas.\n\nComandos: /status, /test, /help")
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
