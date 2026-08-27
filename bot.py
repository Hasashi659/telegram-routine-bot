"""
Bot de Telegram para notificaciones de rutina
Desplegar en Render.com para 24/7
"""

import os
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

BOT_TOKEN = os.environ.get('BOT_TOKEN') or '8866031857:AAFebwtF2BtmzQNYJQnT6t2r1ntqH38fhDo'
OWNER_CHAT_ID = os.environ.get('CHAT_ID') or '6613206978'

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

def time_to_minutes(time_str):
    """Convertir HH:MM a minutos desde medianoche"""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m

# ============================================
# SISTEMA DE NOTIFICACIONES INTELIGENTE
# ============================================

def check_and_notify():
    """Verificar y enviar notificaciones según la lógica"""
    now = get_current_time()
    now_str = get_current_time_str()
    now_minutes = time_to_minutes(now_str)
    current_task, current_idx = get_current_task()
    next_task, next_idx = get_next_task()
    
    logger.info(f"Check: now={now_str}, now_minutes={now_minutes}, current={current_task['task']}, next={next_task['task'] if next_task else 'N/A'}")
    
    notifications = []
    
    # ========================================
    # 1. ALERTA 5 MINUTOS ANTES
    # ========================================
    if next_task:
        next_minutes = time_to_minutes(next_task["time"])
        diff = next_minutes - now_minutes
        
        if diff == 5:
            notifications.append({
                "type": "warning_5min",
                "message": f"""⏰ <b>5 MINUTOS</b>

<b>Prepárate para:</b> {next_task['emoji']} {next_task['task']}
<b>Empieza a las:</b> {next_task['time']}

¡Quedan 5 minutos!"""
            })
        
        elif diff == 2:
            notifications.append({
                "type": "warning_2min",
                "message": f"""🚨 <b>2 MINUTOS</b>

<b>Ya empieza:</b> {next_task['emoji']} {next_task['task']}
<b>A las:</b> {next_task['time']}

¡Prepárate ahora!"""
            })
    
    # ========================================
    # 2. TAREA EMPEZÓ (hora exacta)
    # ========================================
    if now_str in [t["time"] for t in ROUTINE]:
        progress = get_progress()
        end_time = next_task["time"] if next_task else "Fin"
        
        notifications.append({
            "type": "task_started",
            "message": f"""🔔 <b>TAREA INICIADA</b>

<b>Ahora:</b> {current_task['emoji']} {current_task['task']}
<b>Horario:</b> {current_task['time']} - {end_time}
📊 Progreso: {progress}%"""
        })
    
    # ========================================
    # 3. CADA 20 MINUTOS - RECORDATORIO
    # ========================================
    # Calcular minutos desde que empezó la tarea actual
    current_start_minutes = time_to_minutes(current_task["time"])
    minutes_in_task = now_minutes - current_start_minutes
    
    # Enviar cada 20 minutos (0, 20, 40, 60...)
    if minutes_in_task >= 0 and minutes_in_task % 20 == 0:
        remaining = get_minutes_until(next_task["time"]) if next_task else 0
        
        notifications.append({
            "type": "reminder_20min",
            "message": f"""📍 <b>RECORDATORIO</b>

<b>Tarea actual:</b> {current_task['emoji']} {current_task['task']}
<b>Tiempo en tarea:</b> {minutes_in_task} min
<b>Faltan:</b> {remaining} min para siguiente
📊 Progreso: {get_progress()}%"""
        })
    
    # ========================================
    # 4. BUENOS DÍAS (05:30)
    # ========================================
    if now_str == "05:30":
        date = now.strftime("%A %d de %B")
        notifications.append({
            "type": "morning",
            "message": f"""🌅 <b>¡BUENOS DÍAS!</b>

<b>Fecha:</b> {date}

<b>Rutina de hoy:</b>
🧠 05:30 - Despertar
💪 06:30 - Ejercicio
💼 08:00 - Trabajo
💻 13:00 - Vibecoding
📐 19:00 - Estudio

¡Que tengas un día productivo!"""
        })
    
    # ========================================
    # 5. BUENAS NOCHES (22:00)
    # ========================================
    if now_str == "22:00":
        progress = get_progress()
        notifications.append({
            "type": "night",
            "message": f"""🌙 <b>BUENAS NOCHES</b>

<b>Progreso de hoy:</b> {progress}%

Descansa bien. ¡Mañana un nuevo día!"""
        })
    
    # Enviar todas las notificaciones
    for notif in notifications:
        logger.info(f"Enviando notificación: {notif['type']}")
        send_message(notif["message"])
    
    logger.info(f"Total notificaciones enviadas: {len(notifications)}")
    return notifications

# ============================================
# SERVIDOR WEB
# ============================================

app = Flask(__name__)

@app.route('/')
def home():
    """Endpoint principal"""
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
    """Endpoint para cron - SIEMPRE envía estado"""
    current, _ = get_current_task()
    next_task, _ = get_next_task()
    minutes = get_minutes_until(next_task["time"]) if next_task else 0
    progress = get_progress()
    
    # SIEMPRE enviar estado actual
    msg = f"""📍 <b>ESTADO</b> {get_current_time_str()}

<b>Ahora:</b> {current['emoji']} {current['task']}
<b>Próxima:</b> {next_task['task'] if next_task else 'N/A'} (en {minutes} min)
📊 {progress}%"""
    
    send_message(msg)
    
    # Además, alertas especiales
    check_and_notify()
    
    return jsonify({
        "status": "checked",
        "time": get_current_time().isoformat(),
        "current_task": current["task"]
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
    
    msg = f"""📊 <b>ESTADO</b>

<b>Ahora:</b> {current['emoji']} {current['task']}
<b>Próxima:</b> {next_task['task'] if next_task else 'N/A'} ({minutes} min)
<b>Progreso:</b> {progress}%"""
    
    send_message(msg)
    return jsonify({"status": "sent"})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Webhook para recibir mensajes - SOLO procesa del dueño"""
    data = request.get_json()
    
    if not data:
        return jsonify({"status": "no data"})
    
    if data.get("message", {}).get("from", {}).get("id") != int(OWNER_CHAT_ID):
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
    
    # Mensaje de inicio
    send_message("🤖 <b>Bot 24/7 ONLINE</b>\n\n✅ 5 min antes de cada tarea\n✅ Cuando empieza la tarea\n✅ Cada 20 min recordatorio\n\nComandos: /status, /test, /help")
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
