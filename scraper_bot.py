import requests
import json
import base64
from datetime import datetime, timedelta, timezone
import re
import time
import urllib.parse 
import os

# ==========================================================
# 1. PANEL DE CONFIGURACIÓN GENERAL (KAMIKAZE TELEGRAM)
# ==========================================================
NOMBRE_MARCA = "Fútbol Libre TV"
DOMINIO_PRINCIPAL = "www.balonlibre.blog"
BOT_TOKEN_TELEGRAM = os.environ.get("MI_TOKEN_SECRETO") 
CANAL_ID_TELEGRAM = "@balonlibre" 

DOMINIOS_INDEXNOW = [
    {
        "host": "www.balonlibre.blog",
        "key": "391254a6e96a48188f3b6bb64a85220b",
        "keyLocation": "https://www.balonlibre.blog/391254a6e96a48188f3b6bb64a85220b"
    },
    {
        "host": "www.balonlibre.blog",
        "key": "b0fb4526395e43b684ad48ba4c6a7902", 
        "keyLocation": "https://www.balonlibre.blog/b0fb4526395e43b684ad48ba4c6a7902"
    },
    {
        "host": "www.balonlibre.blog",
        "key": "d6e9e3bad3ca42828e74cdeba215d5e7", 
        "keyLocation": "https://www.balonlibre.blog/d6e9e3bad3ca42828e74cdeba215d5e7"
    }
]

# ==========================================================
# 2. ENLACES DE FUENTES Y RESPALDOS (CASCADA)
# ==========================================================
FUENTES_AGENDA = [
    "https://la18hd.su//eventos/json/agenda123.json", # FUENTE PRINCIPAL
    "https://futbollibretv.org.pe/diaries.json?v",    # Respaldo 1
    "https://agenda18.com/agenda.json",               # Respaldo 2
]

API_BANDERAS = "https://agenda18.com/agenda.json"
BASE_DOMAIN_IMG = "https://img.agenda18.com"
DOMINIO_LIMPIO_ACTUAL = "la20hd.com" 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# ==========================================================
# 3. LÓGICA DE EXTRACCIÓN Y BANDERAS
# ==========================================================
def obtener_bandera(liga, encuentro):
    texto = (liga + " " + encuentro).lower()
    if "f1 " in texto or "formula 1" in texto or "fórmula 1" in texto or "f2 " in texto: return "https://cdn-icons-png.flaticon.com/512/3753/3753230.png"
    if "motogp" in texto or "moto gp" in texto: return "https://cdn-icons-png.flaticon.com/512/3204/3204646.png"
    if "rugby" in texto: return "https://cdn-icons-png.flaticon.com/512/4163/4163653.png"
    if "golf" in texto: return "https://cdn-icons-png.flaticon.com/512/5751/5751090.png"
    if "knockout" in texto or "boxeo" in texto or "ufc" in texto: return "https://cdn-icons-png.flaticon.com/512/3349/3349372.png"
    if "hockey" in texto: return "https://cdn-icons-png.flaticon.com/512/6253/6253160.png"
    if "tenis" in texto or "tennis" in texto: return "https://cdn-icons-png.flaticon.com/512/3312/3312932.png"
    if "básquet" in texto or "baloncesto" in texto or "nba" in texto: return "https://cdn-icons-png.flaticon.com/512/3311/3311822.png"
    if "nfl" in texto or "fútbol americano" in texto: return "https://cdn-icons-png.flaticon.com/512/123/123969.png"
    if "béisbol" in texto or "mlb" in texto: return "https://cdn-icons-png.flaticon.com/512/3311/3311818.png"

    if "champions" in texto or "campeones de la uefa" in texto: return "https://cdn-icons-png.flaticon.com/512/520/520786.png"
    if "libertadores" in texto: return "https://cdn-icons-png.flaticon.com/512/1043/1043444.png"
    if "sudamericana" in texto: return "https://cdn-icons-png.flaticon.com/512/3112/3112946.png"
    if "concacaf" in texto: return "https://cdn-icons-png.flaticon.com/512/9903/9903672.png" 
    if "afc" in texto or "asia" in texto: return "https://cdn-icons-png.flaticon.com/512/6104/6104033.png"
    if "fifa" in texto or "mundial" in texto or "conmebol" in texto or "clasificatorias" in texto: return "https://cdn-icons-png.flaticon.com/512/323/323326.png"

    if "perú" in texto or "liga 1" in texto or "peruano" in texto or "alianza" in texto or "cristal" in texto or "universitario" in texto: return "https://flagcdn.com/w40/pe.png"
    if "argentina" in texto or "liga profesional" in texto or "copa de la liga" in texto or "boca" in texto or "river" in texto or "reserva" in texto: return "https://flagcdn.com/w40/ar.png"
    if "mexic" in texto or "liga mx" in texto or "américa" in texto or "cruz azul" in texto or "chivas" in texto: return "https://flagcdn.com/w40/mx.png"
    if "colombia" in texto or "betplay" in texto or "primera a" in texto or "nacional" in texto or "millonarios" in texto: return "https://flagcdn.com/w40/co.png"
    if "chile" in texto or "campeonato nacional" in texto or "colo colo" in texto or "u de chile" in texto: return "https://flagcdn.com/w40/cl.png"
    if "uruguay" in texto or "peñarol" in texto or "nacional" in texto or "segunda división" in texto: return "https://flagcdn.com/w40/uy.png"
    if "ecuador" in texto or "ligapro" in texto or "barcelona sc" in texto or "emelec" in texto: return "https://flagcdn.com/w40/ec.png"
    if "brasil" in texto or "brasileirão" in texto or "paulista" in texto or "flamengo" in texto or "palmeiras" in texto: return "https://flagcdn.com/w40/br.png"
    if "usa" in texto or "mls" in texto or "estados unidos" in texto or "inter miami" in texto: return "https://flagcdn.com/w40/us.png"
    if "españa" in texto or "laliga" in texto or "copa del rey" in texto or "real madrid" in texto or "barcelona" in texto: return "https://flagcdn.com/w40/es.png"
    if "inglaterra" in texto or "premier" in texto or "championship" in texto or "fa cup" in texto or "liverpool" in texto or "city" in texto: return "https://flagcdn.com/w40/gb-eng.png"
    if "italia" in texto or "serie a" in texto or "juventus" in texto or "milan" in texto or "inter" in texto: return "https://flagcdn.com/w40/it.png"
    if "alemania" in texto or "bundesliga" in texto or "bayern" in texto: return "https://flagcdn.com/w40/de.png"
    if "francia" in texto or "ligue 1" in texto or "psg" in texto: return "https://flagcdn.com/w40/fr.png"
    if "arabia" in texto or "pro league" in texto or "al nassr" in texto: return "https://flagcdn.com/w40/sa.png"
    
    return "https://cdn-icons-png.flaticon.com/512/53/53283.png"

def procesar_fecha(fecha_str, hora_str):
    try:
        hora_str = str(hora_str)[:5] if hora_str else "00:00"
        fecha_hora_texto = f"{fecha_str} {hora_str}"
        fecha_obj = datetime.strptime(fecha_hora_texto, "%Y-%m-%d %H:%M")
        tz_origen = timezone(timedelta(hours=-5)) 
        fecha_obj = fecha_obj.replace(tzinfo=tz_origen)
        utc_obj = fecha_obj.astimezone(timezone.utc)
        return utc_obj.strftime("%Y-%m-%dT%H:%M:%SZ"), utc_obj
    except Exception as e:
        now_utc = datetime.now(timezone.utc)
        return now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"), now_utc

def extraer_partidos():
    timestamp = int(time.time() * 1000)
    print(f"[*] FASE 1: Buscando agenda en cascada...")
    datos_json = None
    
    for url_fuente in FUENTES_AGENDA:
        url_con_timestamp = f"{url_fuente}?_={timestamp}"
        print(f"    -> Intentando conectar: {url_fuente[:50]}...")
        try:
            respuesta = requests.get(url_con_timestamp, headers=HEADERS, timeout=10)
            respuesta.raise_for_status() 
            posible_json = respuesta.json()
            
            if isinstance(posible_json, dict):
                posible_json = posible_json.get("data", posible_json.get("record", posible_json.get("response", [])))

            if isinstance(posible_json, list) and len(posible_json) > 0:
                print(f"    [+] ¡ÉXITO! Agenda descargada desde: {url_fuente}")
                datos_json = posible_json
                break 
            else:
                print(f"    [!] Conectó, pero la agenda estaba vacía.")
                
        except Exception as e:
            print(f"    [X] Falló esta fuente. Pasando a la siguiente... ({e})")
            continue 

    if not datos_json:
        print("[X] ERROR CRÍTICO: Todas las fuentes están caídas.")
        return None

    try:
        partidos_agrupados = {}
        for item in datos_json:
            if "attributes" in item:
                data_item = item["attributes"]
                titulo_completo = data_item.get("title", data_item.get("diary_description", "Partido en Vivo")).strip()
                fecha = data_item.get("date", data_item.get("diary_date", data_item.get("date_diary", "")))
                hora = data_item.get("time", data_item.get("diary_time", data_item.get("diary_hour", "")))
                estado = data_item.get("status", "").lower()
            else:
                titulo_completo = item.get("title", "Partido en Vivo").strip()
                fecha = item.get("date", item.get("date_diary", ""))
                hora = item.get("time", item.get("diary_hour", ""))
                estado = item.get("status", "").lower()
                
            # --- FILTRO 1: ESTADO FINALIZADO ---
            if "finalizado" in estado or "terminado" in estado:
                 continue
                 
            datetime_utc, fecha_obj_utc = procesar_fecha(fecha, hora)
            
            # --- FILTRO 2: PARTIDOS FRESCOS (MÁXIMO 120 MINUTOS) ---
            ahora_utc = datetime.now(timezone.utc)
            minutos_transcurridos = (ahora_utc - fecha_obj_utc).total_seconds() / 60
            
            # Si el partido empezó hace más de 2 horas (120 min), lo descartamos
            if minutos_transcurridos > 120:
                continue
            
            if not titulo_completo:
                continue
                
            titulo_para_clave = re.sub(r'[^a-z0-9]', '', titulo_completo.lower())
            match_key = f"{datetime_utc}_{titulo_para_clave}"
            
            if match_key not in partidos_agrupados:
                liga = "Fútbol"
                encuentro = titulo_completo
                if ":" in titulo_completo:
                    partes = titulo_completo.split(":", 1)
                    liga = partes[0].strip()
                    encuentro = partes[1].strip()
                    
                home_team = encuentro
                away_team = ""
                if " vs " in encuentro.lower():
                    equipos = re.split(r'\s+vs\s+', encuentro, flags=re.IGNORECASE)
                    home_team = equipos[0].strip()
                    away_team = equipos[1].strip()
                
                partidos_agrupados[match_key] = {
                    "datetime": datetime_utc,
                    "league": liga,
                    "homeTeam": home_team,
                    "awayTeam": away_team
                }
                
        partidos_extraidos = list(partidos_agrupados.values())
        partidos_extraidos.sort(key=lambda x: x["datetime"])
        
        return partidos_extraidos
        
    except Exception as e:
        print(f"[X] ERROR procesando los datos de la agenda: {e}")
        return None

# ==========================================================
# CEREBRO DE TELEGRAM (MENSAJERO KAMIKAZE AJUSTADO)
# ==========================================================
def notificar_telegram(datos):
    if not datos:
        print("[*] No hay partidos frescos en este momento. Cancelando mensaje de Telegram.")
        return

    ahora_utc = datetime.now(timezone.utc)
    tz_peru = timezone(timedelta(hours=-5))
    ahora_peru = ahora_utc.astimezone(tz_peru)
    
    BOT_TOKEN = os.environ.get("MI_TOKEN_SECRETO")
    CANAL_ID = CANAL_ID_TELEGRAM
    
    # === ROTACIÓN SEO DE ENCABEZADOS (04:00, 10:00, 16:00) ===
    if ahora_peru.hour < 8: # Cubre el gatillo de las 4 AM
        encabezado = "⚽️ <b>FÚTBOL LIBRE TV ▷ Agenda Deportiva de Hoy</b>\n🔥 <i>Partidos en Vivo y Sin Cortes</i> 🔥\n\n"
    elif ahora_peru.hour < 14: # Cubre el gatillo de las 10 AM
        encabezado = "🔴 <b>ROJA DIRECTA EN VIVO ▷ Partidos Hoy</b>\n🔥 <i>Transmisión Online y Sin Interrupciones</i> 🔥\n\n"
    else: # Cubre el gatillo de las 4 PM (16:00)
        encabezado = "📺 <b>ALTERNATIVA PELOTA LIBRE Y PIRLO TV ▷ En Vivo</b>\n🔥 <i>Los mejores encuentros de la jornada</i> 🔥\n\n"
    
    mensaje = encabezado
    
    partidos_mostrados = 0
    for partido in datos:
        if partidos_mostrados >= 6: # Mostramos máximo los 6 mejores partidos frescos
            break
            
        hora_local = partido['datetime'][11:16] 
        
        liga = str(partido['league']).replace('<', '').replace('>', '').replace('&', 'y')
        local = str(partido['homeTeam']).replace('<', '').replace('>', '').replace('&', 'y')
        visita = str(partido['awayTeam']).replace('<', '').replace('>', '').replace('&', 'y')

        mensaje += f"🏆 {liga}\n"
        mensaje += f"⚽ {local} vs {visita}\n"
        mensaje += f"⏰ {hora_local} (UTC)\n\n"
        
        partidos_mostrados += 1

    # === PIE DE PÁGINA (FOOTER SEO) ===
    mensaje += "📺 <b>VER PARTIDOS AQUÍ (Alternativa Oficial):</b>\n"
    mensaje += f"👉 🔗 <a href='https://{DOMINIO_PRINCIPAL}/'>https://{DOMINIO_PRINCIPAL}/</a>\n"
    
    url_telegram = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CANAL_ID,
        "text": mensaje,
        "parse_mode": "HTML", 
        "disable_web_page_preview": True 
    }
    
    try:
        res = requests.post(url_telegram, json=payload)
        if res.status_code == 200:
            print("[+] ¡Mensaje agresivo SEO enviado a Telegram con éxito!")
        else:
            print(f"[X] Error API Telegram (Status {res.status_code}): {res.text}")
    except Exception as e:
        print(f"[X] Error de conexión enviando a Telegram: {e}")

# ==========================================================
# CEREBRO INDEXNOW: PING AUTOMÁTICO AL BUSCADOR (MULTIDOMINIO)
# ==========================================================
def avisar_indexnow():
    if not DOMINIOS_INDEXNOW:
        return
        
    print("\n[*] Avisando a IndexNow (Bing/Yandex) para todos los dominios...")
    url_api = "https://api.indexnow.org/indexnow"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    
    for sitio in DOMINIOS_INDEXNOW:
        host = sitio.get("host")
        key = sitio.get("key")
        key_location = sitio.get("keyLocation")
        
        if not host or not key or key == "PON_LA_CLAVE_AQUI":
            continue
            
        payload = {
            "host": host,
            "key": key,
            "keyLocation": key_location,
            "urlList": [ f"https://{host}/" ]
        }
        
        try:
            res = requests.post(url_api, json=payload, headers=headers, timeout=10)
            if res.status_code in [200, 202]:
                print(f"    [+] ¡Éxito! IndexNow notificado para: {host}")
            else:
                print(f"    [X] Error en {host}: {res.status_code} - {res.text}")
        except Exception as e:
            pass

if __name__ == "__main__":
    print("===================================================================")
    print("   BOT KAMIKAZE TELEGRAM: EJECUCIÓN ÚNICA AUTOMÁTICA                 ")
    print("===================================================================")
    
    ahora = datetime.now().strftime("%H:%M:%S")
    print(f"\n--- INICIANDO EXTRACCIÓN DE PARTIDOS FRESCOS A LAS {ahora} ---")
    
    datos = extraer_partidos()
    
    if datos:
        notificar_telegram(datos)
    else:
        print("[!] No hay partidos frescos. Abortando misión.")

    avisar_indexnow()
        
    print(f"\n[*] Proceso de Spam SEO finalizado a las {datetime.now().strftime('%H:%M:%S')}.")
