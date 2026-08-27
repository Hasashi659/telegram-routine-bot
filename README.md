# Deploy en Render.com

## Pasos (5 minutos)

### 1. Crear cuenta en Render
- Ve a https://render.com
- Regístrate gratis con GitHub o email

### 2. Crear repositorio en GitHub
1. Ve a https://github.com
2. Crea un nuevo repositorio: `telegram-routine-bot`
3. Sube los archivos de esta carpeta

### 3. Crear Web Service en Render
1. En Render, haz clic en **"New +"**
2. Selecciona **"Background Worker"** (o **"Web Service"**)
3. Conecta tu repositorio de GitHub
4. Configura:
   - **Name**: `telegram-routine-bot`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:10000 bot:app`
   - **Instance Type**: `Free`

### 4. Agregar Variables de Entorno
En la sección **"Environment"**:
```
BOT_TOKEN = 8872994414:AAFBL1OFjUSOSmEcZHwKjeXWllvztHZUZUI
CHAT_ID = 6613206978
```

### 5. Desplegar
- Haz clic en **"Create Web Service"**
- Espera 2-3 minutos a que se despliegue
- ¡Listo! El bot está corriendo 24/7

## Verificar
- Ve a la URL que te da Render
- Debería mostrar: `{"status": "running"}`
- Revisa tu Telegram: debería llegar un mensaje de "Bot 24/7 ONLINE"

## Archivos
| Archivo | Descripción |
|---------|-------------|
| `bot.py` | Script principal |
| `requirements.txt` | Dependencias |
| `Dockerfile` | Configuración de Docker |

## Costo
- **Gratis**: 750 horas/mes (suficiente para 24/7)
- Si se acaban, se pausa hasta el siguiente mes

## Solución de Problemas
- Si el bot no responde, revisa los logs en Render
- Verifica que las variables de entorno estén correctas
- Asegúrate de haber enviado `/start` a tu bot
