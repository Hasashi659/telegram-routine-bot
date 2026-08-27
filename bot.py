"""
Bot de Telegram para notificaciones de rutina v3
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
# DÍAS DE LA SEMANA (0=Lunes, 6=Domingo)
# ============================================

DAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
WEEKDAY = ["L", "M", "X", "J", "V", "S", "D"]

# ============================================
# ACTIVIDADES POR DÍA DE LA SEMANA
# ============================================

def get_gym_exercise(day):
    """Ejercicio de gimnasio según el día"""
    gym = {
        0: "Gym: Pecho + tríceps",      # Lunes
        1: "Gym: Espalda + bíceps",     # Martes
        2: "Gym: Pierna + abs",         # Miércoles
        3: "Gym: Pecho + tríceps",      # Jueves
        4: "Gym: Espalda + bíceps",     # Viernes
        5: "Gym: Pierna completa",      # Sábado
        6: "Estiramientos + movilidad"  # Domingo
    }
    return gym.get(day, "Ejercicio")

def get_morning_routine(day):
    """Rutina de la mañana según el día"""
    return {
        "rosary": "Rezar Rosario (26min + 4min silencio)",
        "visualization": "Visualización del día" if day < 5 else ("Visualización semanal" if day == 5 else "Journaling reflexión dominical")
    }

def get_work_activity(day):
    """Actividad laboral/estudio según el día"""
    if day < 5:
        return "Trabajo presencial"
    else:
        return "Estudio/Proyecto"

def get_vibecoding_blocks(day):
    """Bloques de vibecoding"""
    if day < 5:
        return [
            {"time": "13:00", "task": "Vibecoding Block 1 (2h)", "emoji": "💻", "detail": "Deep work: proyecto principal"},
            {"time": "15:00", "task": "Break 15min", "emoji": "☕", "detail": "Descanso activo"},
            {"time": "15:15", "task": "Vibecoding Block 2 (2h)", "emoji": "💻", "detail": "Deep work: segundo proyecto"},
            {"time": "17:15", "task": "Break 15min", "emoji": "☕", "detail": "Descanso activo"},
            {"time": "17:30", "task": "Vibecoding Block 3 (1.5h)", "emoji": "💻", "detail": "Learning + exploración IA"}
        ]
    else:
        return [
            {"time": "13:00", "task": "Vibecoding (mismo esquema)", "emoji": "💻", "detail": "Deep work flexible"},
            {"time": "15:00", "task": "Break 15min", "emoji": "☕", "detail": "Descanso activo"},
            {"time": "15:15", "task": "Vibecoding continuación", "emoji": "💻", "detail": "Deep work flexible"},
            {"time": "17:15", "task": "Break 15min", "emoji": "☕", "detail": "Descanso activo"},
            {"time": "17:30", "task": "Vibecoding Block 3 (1.5h)", "emoji": "💻", "detail": "Learning + exploración IA"}
        ]

def get_english_focus(day):
    """Enfoque de inglés según el día"""
    english = {
        0: "Inglés: listening (Podcasts, YouTube)",        # Lunes
        1: "Inglés: grammar (Libro, ejercicios)",          # Martes
        2: "Inglés: speaking (Práctica, app)",             # Miércoles
        3: "Inglés: vocabulary (Anki, flashcards)",        # Jueves
        4: "Inglés: writing (Diario, ejercicios)",         # Viernes
        5: "Inglés: libre (Películas, series)",            # Sábado
        6: "Inglés: libre (Películas, series)"             # Domingo
    }
    return english.get(day, "Inglés: libre")

def get_math_topic(day):
    """Tema de matemáticas según el día"""
    math = {
        0: "Matemáticas: Álgebra",           # Lunes
        1: "Matemáticas: Geometría",         # Martes
        2: "Matemáticas: Estadística",       # Miércoles
        3: "Matemáticas: Cálculo",           # Jueves
        4: "Matemáticas: Aplicación práctica", # Viernes
        5: "Matemáticas: Repaso/Ejercicios", # Sábado
        6: "Matemáticas: Repaso/Ejercicios"  # Domingo
    }
    return math.get(day, "Matemáticas")

def get_finance_topic(day):
    """Tema de finanzas según el día"""
    finance = {
        0: "Finanzas: Teoría financiera",        # Lunes
        1: "Finanzas: Inversiones",              # Martes
        2: "Finanzas: Presupuesto",              # Miércoles
        3: "Finanzas: Análisis fundamental",     # Jueves
        4: "Finanzas: Revisión semanal",         # Viernes
        5: "Finanzas: Investigación profunda",   # Sábado
        6: "Finanzas: Planificación financiera"  # Domingo
    }
    return finance.get(day, "Finanzas")

def get_trading_topic(day):
    """Tema de trading según el día"""
    trading = {
        0: "Trading: Análisis de mercado",       # Lunes
        1: "Trading: Patrones de velas",         # Martes
        2: "Trading: Estrategias de entrada",    # Miércoles
        3: "Trading: Gestión de riesgo",         # Jueves
        4: "Trading: Journal de trades",         # Viernes
        5: "Trading: Backtesting/Práctica",      # Sábado
        6: "Trading: Análisis semanal"           # Domingo
    }
    return trading.get(day, "Trading")

def get_video_topic(day):
    """Tema de videos según el día"""
    videos = {
        0: "Videos: IA/Nuevas herramientas",    # Lunes
        1: "Videos: Ventas/Comunicación",       # Martes
        2: "Videos: Instrumento musical",       # Miércoles
        3: "Videos: Productividad",             # Jueves
        4: "Videos: Emprendimiento",            # Viernes
        5: "Videos: Proyecto personal",         # Sábado
        6: "Videos: Planificación"              # Domingo
    }
    return videos.get(day, "Videos libre")

def get_weekend_study(day):
    """Actividades de estudio fines de semana"""
    if day == 5:  # Sábado
        return [
            {"time": "19:00", "task": "Estudio profundo", "emoji": "📚"},
            {"time": "19:30", "task": "Práctica", "emoji": "🔧"},
            {"time": "20:00", "task": "Proyecto personal", "emoji": "🚀"},
            {"time": "20:30", "task": "Práctica", "emoji": "🔧"},
            {"time": "21:00", "task": "Lectura libre", "emoji": "📖"},
            {"time": "21:30", "task": "Videos libre", "emoji": "🎬"}
        ]
    elif day == 6:  # Domingo
        return [
            {"time": "19:00", "task": "Repaso semanal", "emoji": "📋"},
            {"time": "19:30", "task": "Práctica", "emoji": "🔧"},
            {"time": "20:00", "task": "Plan semana siguiente", "emoji": "📅"},
            {"time": "20:30", "task": "Práctica", "emoji": "🔧"},
            {"time": "21:00", "task": "Resumen semanal", "emoji": "📊"},
            {"time": "21:30", "task": "Videos libre", "emoji": "🎬"}
        ]
    return []

# ============================================
# RUTINA COMPLETA POR DÍA
# ============================================

def get_routine_for_day(day):
    """Obtener rutina completa para un día específico"""
    routine = []
    
    # MADRUGADA (misma todos los días)
    routine.append({"time": "05:30", "task": "Despertar sin celular", "emoji": "🧠"})
    routine.append({"time": "05:45", "task": "Rezar Rosario (30min)", "emoji": "✝️"})
    routine.append({"time": "06:15", "task": get_morning_routine(day)["visualization"], "emoji": "🎯"})
    
    # EJERCICIO (cambia por día) - 06:30 a 07:15
    routine.append({"time": "06:30", "task": get_gym_exercise(day), "emoji": "💪"})
    routine.append({"time": "07:15", "task": "Ducharse + aseo", "emoji": "🚿"})
    
    # DESAYUNO + INGLÉS
    routine.append({"time": "07:30", "task": "Desayuno + " + get_english_focus(day), "emoji": "🍳"})
    
    # TRABAJO/ESTUDIO
    routine.append({"time": "08:00", "task": get_work_activity(day), "emoji": "💼"})
    
    # ALMUERZO
    routine.append({"time": "12:00", "task": "Almuerzo + caminar", "emoji": "🍽️"})
    
    # VIBECODING (varía por día)
    vibecoding = get_vibecoding_blocks(day)
    for block in vibecoding:
        routine.append(block)
    
    # ACTIVIDADES DE TARDE (varían por día)
    if day < 5:  # Lunes a Viernes
        routine.append({"time": "19:00", "task": get_math_topic(day), "emoji": "📐"})
        routine.append({"time": "19:30", "task": get_english_focus(day), "emoji": "🇬🇧"})
        routine.append({"time": "20:00", "task": get_finance_topic(day), "emoji": "💰"})
        routine.append({"time": "20:30", "task": get_trading_topic(day), "emoji": "📈"})
        routine.append({"time": "21:00", "task": "Lectura técnica (30min)", "emoji": "📖"})
        routine.append({"time": "21:30", "task": get_video_topic(day), "emoji": "🎬"})
    else:  # Fines de semana
        weekend = get_weekend_study(day)
        for activity in weekend:
            routine.append(activity)
    
    # NOCHE (misma todos los días)
    routine.append({"time": "22:00", "task": "Dormir", "emoji": "😴"})
    
    return routine

# ============================================
# RUTINA GENÉRICA (para compatibilidad)
# ============================================

ROUTINE = get_routine_for_day(datetime.now(TZ_COLOMBIA).weekday())

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

def get_current_day():
    """Obtener día actual (0=Lunes, 6=Domingo)"""
    return get_current_time().weekday()

def get_current_day_name():
    """Obtener nombre del día actual"""
    return DAY_NAMES[get_current_day()]

def get_current_routine():
    """Obtener rutina del día actual"""
    return get_routine_for_day(get_current_day())

def get_current_task():
    """Obtener tarea actual"""
    routine = get_current_routine()
    current_time = get_current_time_str()
    for i in range(len(routine) - 1, -1, -1):
        if current_time >= routine[i]["time"]:
            return routine[i], i
    return routine[0], 0

def get_next_task():
    """Obtener siguiente tarea"""
    routine = get_current_routine()
    current_time = get_current_time_str()
    for i, task in enumerate(routine):
        if current_time < task["time"]:
            return task, i
    return routine[0], 0

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
    routine = get_current_routine()
    current_time = get_current_time_str()
    completed = sum(1 for t in routine if current_time >= t["time"])
    return int((completed / len(routine)) * 100)

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
    day = get_current_day()
    day_name = get_current_day_name()
    
    logger.info(f"Check: {day_name} {now_str}, current={current_task['task']}, next={next_task['task'] if next_task else 'N/A'}")
    
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

<b>Día:</b> {day_name}
<b>Prepárate para:</b> {next_task['emoji']} {next_task['task']}
<b>Empieza a las:</b> {next_task['time']}

¡Quedan 5 minutos!"""
            })
        
        elif diff == 2:
            notifications.append({
                "type": "warning_2min",
                "message": f"""🚨 <b>2 MINUTOS</b>

<b>Día:</b> {day_name}
<b>Ya empieza:</b> {next_task['emoji']} {next_task['task']}
<b>A las:</b> {next_task['time']}

¡Prepárate ahora!"""
            })
    
    # ========================================
    # 2. TAREA EMPEZÓ (hora exacta)
    # ========================================
    routine = get_current_routine()
    if now_str in [t["time"] for t in routine]:
        progress = get_progress()
        end_time = next_task["time"] if next_task else "Fin"
        
        notifications.append({
            "type": "task_started",
            "message": f"""🔔 <b>TAREA INICIADA</b>

<b>Día:</b> {day_name}
<b>Ahora:</b> {current_task['emoji']} {current_task['task']}
<b>Horario:</b> {current_task['time']} - {end_time}
📊 Progreso: {progress}%"""
        })
    
    # ========================================
    # 3. CADA 20 MINUTOS - RECORDATORIO
    # ========================================
    current_start_minutes = time_to_minutes(current_task["time"])
    minutes_in_task = now_minutes - current_start_minutes
    
    if minutes_in_task >= 0 and minutes_in_task % 20 == 0:
        remaining = get_minutes_until(next_task["time"]) if next_task else 0
        
        notifications.append({
            "type": "reminder_20min",
            "message": f"""📍 <b>RECORDATORIO</b>

<b>Día:</b> {day_name}
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
        gym = get_gym_exercise(day)
        english = get_english_focus(day)
        math = get_math_topic(day)
        
        notifications.append({
            "type": "morning",
            "message": f"""🌅 <b>¡BUENOS DÍAS!</b>

<b>Fecha:</b> {date}
<b>Día:</b> {day_name}

<b>Rutina de hoy:</b>
✝️ 05:45 - Rezar Rosario
💪 07:00 - {gym}
💼 08:30 - {get_work_activity(day)}
💻 13:00 - Vibecoding
📐 19:00 - {math}

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

<b>Día:</b> {day_name}
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
    day = get_current_day()
    day_name = get_current_day_name()
    
    return jsonify({
        "status": "running",
        "day": day_name,
        "current_task": current["task"],
        "next_task": next_task["task"] if next_task else "N/A",
        "minutes_until_next": minutes,
        "progress": f"{progress}%",
        "time": get_current_time().isoformat(),
        "timezone": "America/Bogota (UTC-5)",
        "gym_today": get_gym_exercise(day),
        "english_today": get_english_focus(day),
        "math_today": get_math_topic(day),
        "finance_today": get_finance_topic(day),
        "trading_today": get_trading_topic(day)
    })

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/check')
def check():
    """Endpoint para cron - solo envía notificaciones necesarias"""
    notifications = check_and_notify()
    
    return jsonify({
        "status": "checked",
        "day": get_current_day_name(),
        "time": get_current_time().isoformat(),
        "notifications_sent": len(notifications)
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
    day = get_current_day()
    day_name = get_current_day_name()
    
    msg = f"""📊 <b>ESTADO</b>

<b>Día:</b> {day_name}
<b>Ahora:</b> {current['emoji']} {current['task']}
<b>Próxima:</b> {next_task['task'] if next_task else 'N/A'} ({minutes} min)
<b>Progreso:</b> {progress}%

<b>Hoy toca:</b>
💪 {get_gym_exercise(day)}
📐 {get_math_topic(day)}
🇬🇧 {get_english_focus(day)}"""
    
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
            day = get_current_day()
            day_name = get_current_day_name()
            
            msg = f"""📊 <b>ESTADO</b>

<b>Día:</b> {day_name}
<b>Ahora:</b> {current['emoji']} {current['task']}
<b>Próxima:</b> {next_task['task'] if next_task else 'N/A'} ({minutes} min)
<b>Progreso:</b> {progress}%

<b>Hoy toca:</b>
💪 {get_gym_exercise(day)}
📐 {get_math_topic(day)}
🇬🇧 {get_english_focus(day)}"""
            
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
    logger.info("Iniciando bot v3...")
    
    day = get_current_day()
    day_name = get_current_day_name()
    
    # Mensaje de inicio
    send_message(f"""🤖 <b>Bot 24/7 ONLINE - v3</b>

📅 <b>Día:</b> {day_name}
💪 <b>Gym hoy:</b> {get_gym_exercise(day)}
📐 <b>Matemáticas:</b> {get_math_topic(day)}
🇬🇧 <b>Inglés:</b> {get_english_focus(day)}

✅ 5 min antes de cada tarea
✅ Cuando empieza la tarea
✅ Cada 20 min recordatorio

Comandos: /status, /test, /help""")
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
