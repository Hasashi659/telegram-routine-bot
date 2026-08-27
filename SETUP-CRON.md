# Configurar Cron Job para Bot de Rutina

## Opción 1: cron-job.org (Gratis)

1. Ve a https://cron-job.org
2. Crea una cuenta gratuita
3. Haz clic en **"Create Job"**
4. Configura:
   - **URL:** `https://telegram-routine-bot.onrender.com/check`
   - **Schedule:** Every minute (`* * * * *`)
   - **Request Method:** GET
   - **Job Name:** "Routine Bot Check"
5. Haz clic en **"Save"**

## Opción 2: UptimeRobot (Gratis)

1. Ve a https://uptimerobot.com
2. Crea una cuenta gratuita
3. Haz clic en **"Add New Monitor"**
4. Configura:
   - **Monitor Type:** HTTP(s)
   - **URL:** `https://telegram-routine-bot.onrender.com/check`
   - **Monitoring Interval:** 1 minute
   - **Monitor Name:** "Routine Bot"
5. Haz clic on **"Create Monitor"**

## Opción 3: Jobcord (Gratis)

1. Ve a https://jobcord.net
2. Crea una cuenta
3. Agrega un job:
   - **URL:** `https://telegram-routine-bot.onrender.com/check`
   - **Cron:** `* * * * *`

---

**¿Cuál prefieres usar?** Te guío paso a paso.
