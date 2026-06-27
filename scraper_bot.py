import requests
import json
import base64
from datetime import datetime, timedelta, timezone
import re
import time
import subprocess
import urllib.parse 

# ==========================================================
# 1. CONFIGURACIÓN (Ya no se usa JSONBIN, se usa GitHub)
# ==========================================================
BIN_ID = "69d933e5aaba882197e5950b" 
API_KEY = "$2a$10$fH2AVYqUAGOQm6KLrAcdk.fsTBsZPp7sTDWydhhsWtaYfrLlnAWv."

# ==========================================================
# 2. ENLACES Y RESPALDOS DE LA AGENDA
# ==========================================================
# RED DE RESPALDOS: El bot probará una por una hasta encontrar una que funcione.
FUENTES_AGENDA = [
    "https://la18hd.com/eventos/json/agenda123.json",
    "https://pltvhd.com/diaries.json",               # NUEVO: Respaldo Pelota Libre
    "https://agenda18.com/agenda.json",              # NUEVO: Respaldo Fubolazo
]

API_BANDERAS = "https://agenda18.com/agenda.json"
BASE_DOMAIN_IMG = "https://img.agenda18.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# ==========================================================
# 3. LÓGICA DE BANDERAS (Respaldo visual)
# ==========================================================
def obtener_bandera(liga, encuentro):
    texto = (liga + " " + encuentro).lower()
    
    if "champions" in texto or "campeones de la uefa" in texto: return "https://cdn-icons-png.flaticon.com/512/520/520786.png"
    if "libertadores" in texto: return "https://cdn-icons-png.flaticon.com/512/1043/1043444.png"
    if "sudamericana" in texto: return "https://cdn-icons-png.flaticon.com/512/3112/3112946.png"
    if "concacaf" in texto: return "https://cdn-icons-png.flaticon.com/512/9903/9903672.png" 
    if "afc" in texto or "asia" in texto: return "https://cdn-icons-png.flaticon.com/512/6104/6104033.png"
    if "fifa" in texto or "mundial" in texto or "conmebol" in texto or "clasificatorias" in texto: return "https://cdn-icons-png.flaticon.com/512/323/323326.png"

    if "perú" in texto or "liga 1" in texto or "peruano" in texto or "alianza" in texto or "cristal" in texto or "universitario" in texto: return "https://flagcdn.com/w40/pe.png"
    if "argentina" in texto or "liga profesional" in texto or "copa de la liga" in texto or "boca" in texto or "river" in texto: return "https://flagcdn.com/w40/ar.png"
    if "mexic" in texto or "liga mx" in texto or "américa" in texto or "cruz azul" in texto or "chivas" in texto: return "https://flagcdn.com/w40/mx.png"
    if "colombia" in texto or "betplay" in texto or "primera a" in texto or "nacional" in texto or "millonarios" in texto: return "https://flagcdn.com/w40/co.png"
    if "chile" in texto or "campeonato nacional" in texto or "colo colo" in texto or "u de chile" in texto: return "https://flagcdn.com/w40/cl.png"
    if "uruguay" in texto or "peñarol" in texto or "nacional" in texto: return "https://flagcdn.com/w40/uy.png"
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

def desencriptar_enlace(iframe_str):
    try:
        if 'r=' in str(iframe_str):
            b64_texto = str(iframe_str).split('r=')[1].split('&')[0].split('"')[0]
            url_real = base64.b64decode(b64_texto).decode('utf-8')
            return url_real
    except Exception as e:
        pass
    return iframe_str

def procesar_fecha(fecha_str, hora_str):
    try:
        # Aseguramos que la hora tenga el formato correcto HH:MM eliminando los segundos si los trae (ej. 22:00:00 -> 22:00)
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
    
    print(f"[*] FASE 1: Extrayendo imágenes originales (Banderas)...")
    diccionario_banderas = {}
    try:
        res_banderas = requests.get(f"{API_BANDERAS}?_={timestamp}", headers=HEADERS, timeout=15)
        if res_banderas.status_code == 200:
            datos_banderas = res_banderas.json()
            lista_fubolazo = datos_banderas if isinstance(datos_banderas, list) else datos_banderas.get("data", [])
            for item in lista_fubolazo:
                attrs = item.get("attributes", {})
                titulo = attrs.get("diary_description", "").strip().lower()
                try:
                    ruta_img = attrs.get("country", {}).get("data", {}).get("attributes", {}).get("image", {}).get("data", {}).get("attributes", {}).get("url", "")
                    if ruta_img and titulo:
                        diccionario_banderas[titulo] = ruta_img if ruta_img.startswith("http") else BASE_DOMAIN_IMG + ruta_img
                except:
                    pass
            print(f"    -> Memorizadas {len(diccionario_banderas)} banderas.")
    except Exception as e:
        print(f"[!] Aviso: Error leyendo el servidor de banderas ({e})")

    # =========================================================================
    # FASE 2: EXTRACCIÓN DE AGENDA (CON RED DE RESPALDO Y PROTECCIÓN)
    # =========================================================================
    print(f"[*] FASE 2: Buscando agenda en la red de respaldos...")
    datos_json = None
    
    for url_fuente in FUENTES_AGENDA:
        url_con_timestamp = f"{url_fuente}?_={timestamp}"
        print(f"    -> Intentando conectar a: {url_fuente[:50]}...")
        try:
            respuesta = requests.get(url_con_timestamp, headers=HEADERS, timeout=10)
            respuesta.raise_for_status() 
            posible_json = respuesta.json()
            
            if isinstance(posible_json, dict):
                posible_json = posible_json.get("data", posible_json.get("record", posible_json.get("response", [])))

            if isinstance(posible_json, list) and len(posible_json) > 0:
                print(f"    [+] ¡ÉXITO! Agenda descargada correctamente.")
                datos_json = posible_json
                break 
            else:
                print(f"    [!] Conectó, pero la agenda estaba vacía o en formato bloqueado.")
                
        except Exception as e:
            print(f"    [X] Servidor caído o error de conexión. Pasando al siguiente respaldo...")
            continue 

    if not datos_json:
        print("[X] ERROR CRÍTICO: Todas las páginas de la red de respaldo están caídas en este momento.")
        return None
        
    try:
        partidos_agrupados = {}
        
        for item in datos_json:
            servers_temporales = []
            
            # --- NUEVA LÓGICA: SOPORTE PARA EL ARREGLO 'embeds' DE PLTVHD Y AGENDA18 ---
            if "attributes" in item:
                data_item = item["attributes"]
                titulo_completo = data_item.get("title", data_item.get("diary_description", "Partido en Vivo")).strip()
                
                # Extraemos fecha y hora usando las claves de las imágenes (date_diary, diary_hour)
                fecha = data_item.get("date", data_item.get("diary_date", data_item.get("date_diary", "")))
                hora = data_item.get("time", data_item.get("diary_time", data_item.get("diary_hour", "")))
                estado = data_item.get("status", "").lower()
                
                # 1. Buscar en el arreglo anidado "embeds" -> "data" (Estructura de pltvhd)
                if "embeds" in data_item and "data" in data_item["embeds"]:
                    for embed in data_item["embeds"]["data"]:
                        emb_attrs = embed.get("attributes", {})
                        e_name = emb_attrs.get("embed_name", "Opción")
                        e_iframe = emb_attrs.get("embed_iframe", "")
                        if e_iframe:
                            servers_temporales.append({"name": e_name, "iframe": e_iframe})
                            
                # 2. Buscar formato clásico directo (Por si acaso la web cambia a futuro)
                else:
                    link = data_item.get("link", data_item.get("url", data_item.get("embed_url", data_item.get("iframe", ""))))
                    canal = data_item.get("channel", data_item.get("diary_channel", data_item.get("canal", "")))
                    idioma = data_item.get("language", "Español")
                    if link:
                        c_name = str(canal).strip() if canal else f"Opción ({idioma})"
                        servers_temporales.append({"name": c_name, "iframe": link})
                        
            else:
                # Estructura sin "attributes" (clásica plana)
                titulo_completo = item.get("title", "Partido en Vivo").strip()
                fecha = item.get("date", item.get("date_diary", ""))
                hora = item.get("time", item.get("diary_hour", ""))
                estado = item.get("status", "").lower()
                link = item.get("link", item.get("url", item.get("embed_url", item.get("iframe", ""))))
                canal = item.get("channel", item.get("canal", ""))
                idioma = item.get("language", "Español")
                if link:
                    c_name = str(canal).strip() if canal else f"Opción ({idioma})"
                    servers_temporales.append({"name": c_name, "iframe": link})
            
            if "finalizado" in estado or "terminado" in estado:
                 continue
                 
            datetime_utc, fecha_obj_utc = procesar_fecha(fecha, hora)
            
            # --- FILTRO DE LIMPIEZA: 160 MINUTOS ---
            ahora_utc = datetime.now(timezone.utc)
            minutos_transcurridos = (ahora_utc - fecha_obj_utc).total_seconds() / 60
            
            if minutos_transcurridos > 160:
                continue
            
            if not titulo_completo:
                continue
                
            match_key = f"{fecha}_{hora}_{titulo_completo}"
            
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
                
                bandera_magica = ""
                
                # 1. Búsqueda de imágenes
                titulo_busqueda = titulo_completo.lower()
                for clave_texto, url_logo in diccionario_banderas.items():
                     if (home_team.lower() in clave_texto and away_team.lower() in clave_texto) or (titulo_busqueda in clave_texto) or (clave_texto in titulo_busqueda):
                        bandera_magica = url_logo
                        break
                        
                # 2. Fallback de banderas
                if not bandera_magica:
                    bandera_magica = obtener_bandera(liga, encuentro)

                partidos_agrupados[match_key] = {
                    "datetime": datetime_utc,
                    "flagUrl": bandera_magica,
                    "league": liga,
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "servers": []
                }

            # Procesamiento de todos los servidores/canales extraídos
            for srv in servers_temporales:
                canal_nombre = srv["name"]
                link = srv["iframe"]
                
                # Si el canal sigue sin nombre, lo intentamos sacar de la propia URL
                if ("Opción" in canal_nombre or not canal_nombre) and "stream=" in str(link):
                    try:
                        canal_raw = str(link).split("stream=")[-1].split('"')[0].split('&')[0].replace("_", " ").upper()
                        canal_nombre = f"{canal_raw}"
                    except:
                        pass
                
                url_limpia = desencriptar_enlace(link)
                url_segura = url_limpia.replace("\\/", "/").replace("canales.php", "canal.php")
                
                # Evitar insertar canales duplicados exactos
                existe = False
                for s in partidos_agrupados[match_key]["servers"]:
                    if s["url"] == url_segura and s["name"] == canal_nombre:
                        existe = True
                        break
                        
                if not existe:
                    partidos_agrupados[match_key]["servers"].append({
                        "name": canal_nombre,
                        "channel": canal_nombre,  
                        "url": url_segura,
                        "iframe": link 
                    })
        
        partidos_extraidos = list(partidos_agrupados.values())
        partidos_extraidos.sort(key=lambda x: x["datetime"])
        
        for i, p in enumerate(partidos_extraidos):
            p["id"] = i + 1
            print(f"  -> {p['league']}: {p['homeTeam']} | {len(p['servers'])} links")
            
        return partidos_extraidos
    except Exception as e:
        print(f"[X] ERROR procesando los datos de la agenda: {e}")
        return None

def actualizar_nube(datos):
    if not datos:
        print("[!] No hay datos para subir. La agenda está vacía.")
        datos = []
        
    try:
        with open('agenda.json', 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
        print("[+] Archivo agenda.json guardado localmente.")
        
        print("[*] Conectando con GitHub API...")
        
        # === CONFIGURACIÓN GITHUB ===
        github_token = "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" 
        repo = "mesias010194/bot-futbol-libre"
        file_path = "agenda.json"
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        with open('agenda.json', 'rb') as file:
            content = file.read()
            encoded_content = base64.b64encode(content).decode('utf-8')
            
        get_res = requests.get(url, headers=headers)
        sha = ""
        if get_res.status_code == 200:
            sha = get_res.json()['sha']
            
        data = {
            "message": "Actualización automática de agenda 🔄",
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            data["sha"] = sha
            
        put_res = requests.put(url, headers=headers, data=json.dumps(data))
        
        if put_res.status_code in [200, 201]:
             print("[+] ¡ÉXITO! Agenda publicada en GitHub directamente.")
        else:
             print(f"[X] Error al subir a GitHub: {put_res.status_code} - {put_res.text}")
             
    except Exception as e:
        print(f"[X] Error guardando en GitHub: {e}")

# ==========================================================
# CEREBRO DE TELEGRAM (CORREGIDO Y BLINDADO)
# ==========================================================
def notificar_telegram(datos):
    if not datos:
        return

    print("\n[*] Preparando mensaje automático para Telegram...")
    
    # ⚠️ REEMPLAZA ESTO CON TUS DATOS REALES ⚠️
    BOT_TOKEN = "TU_TOKEN_DE_TELEGRAM_AQUI" 
    CANAL_ID = "@futbol_libre_tv_oficial"
    
    mensaje = "🔥 <b>¡AGENDA DEL DÍA ACTUALIZADA!</b> 🔥\n\n"
    
    partidos_mostrados = 0
    for partido in datos:
        if partidos_mostrados >= 5:
            break
            
        hora_local = partido['datetime'][11:16] 
        
        # Limpieza por seguridad
        liga = str(partido['league']).replace('<', '').replace('>', '').replace('&', 'y')
        local = str(partido['homeTeam']).replace('<', '').replace('>', '').replace('&', 'y')
        visita = str(partido['awayTeam']).replace('<', '').replace('>', '').replace('&', 'y')

        mensaje += f"🏆 {liga}\n"
        mensaje += f"⚽ {local} vs {visita}\n"
        mensaje += f"⏰ {hora_local} (UTC)\n\n"
        
        partidos_mostrados += 1

    mensaje += "👉 <b>¡Míralos todos EN VIVO y SIN CORTES aquí!</b>\n"
    mensaje += "🔗 <a href='https://www.futbolibre.blog'>futbolibre.blog</a>"
    
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
            print("[+] ¡Mensaje enviado a Telegram con éxito!")
        else:
            print(f"[X] Error API Telegram (Status {res.status_code}): {res.text}")
    except Exception as e:
        print(f"[X] Error de conexión enviando a Telegram: {e}")


if __name__ == "__main__":
    print("===================================================================")
    print("   BOT GITHUB ACTIONS: EJECUCIÓN ÚNICA AUTOMÁTICA                  ")
    print("===================================================================")
    
    ahora = datetime.now().strftime("%H:%M:%S")
    print(f"\n--- INICIANDO ESCANEO A LAS {ahora} ---")
    
    datos = extraer_partidos()
    
    if datos is None: 
        datos = []
        
    actualizar_nube(datos)
    
    if datos:
        notificar_telegram(datos)
        
    print(f"\n[*] Escaneo y subida finalizada a las {datetime.now().strftime('%H:%M:%S')}.")
