import requests
import json
import base64
from datetime import datetime, timedelta, timezone
import re
import time
import subprocess

# ==========================================================
# 1. CONFIGURACIÓN DE TU NUBE (JSONBIN.IO) - (Ya no se usa)
BIN_ID = "69d933e5aaba882197e5950b" 
API_KEY = "$2a$10$fH2AVYqUAGOQm6KLrAcdk.fsTBsZPp7sTDWydhhsWtaYfrLlnAWv."

# ==========================================================
# 2. LOS LINKS DE LAS BÓVEDAS (AGENDA FRESCA + FOTOS)
# ==========================================================
API_AGENDA = "https://la18hd.com/eventos/json/agenda123.json"
API_BANDERAS = "https://agenda18.com/agenda.json"
BASE_DOMAIN_IMG = "https://img.agenda18.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
}

# ==========================================================
# 3. CEREBRO DE BANDERAS (Respaldo por si Fubolazo falla)
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
        if 'r=' in iframe_str:
            b64_texto = iframe_str.split('r=')[1].split('&')[0]
            url_real = base64.b64decode(b64_texto).decode('utf-8')
            return url_real
    except Exception as e:
        pass
    return iframe_str

def procesar_fecha(fecha_str, hora_str):
    try:
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
    
    print(f"[*] FASE 1: Extrayendo imágenes originales de Fubolazo...")
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
        print(f"[!] Aviso: Error con banderas ({e})")

    url_con_timestamp = f"{API_AGENDA}?_={timestamp}"
    print(f"[*] FASE 2: Conectando a la agenda súper fresca: {url_con_timestamp[:50]}...")
    try:
        respuesta = requests.get(url_con_timestamp, headers=HEADERS, timeout=15)
        respuesta.raise_for_status() 
        datos_json = respuesta.json()
        
        partidos_agrupados = {}
        
        for item in datos_json:
            titulo_completo = item.get("title", "Partido en Vivo").strip()
            fecha = item.get("date", "")
            hora = item.get("time", "")
            link = item.get("link", "")
            idioma = item.get("language", "Español")
            estado = item.get("status", "").lower()
            
            if "finalizado" in estado or "terminado" in estado:
                 continue
                 
            datetime_utc, fecha_obj_utc = procesar_fecha(fecha, hora)
            
            # --- FILTRO RELOJ: 240 MINUTOS (4 HORAS) ---
            ahora_utc = datetime.now(timezone.utc)
            minutos_transcurridos = (ahora_utc - fecha_obj_utc).total_seconds() / 60
            
            if minutos_transcurridos > 135:
                continue
            
            if not titulo_completo or "Futbol" not in item.get("category", ""):
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
                
                # --- SISTEMA DE ASIGNACIÓN DE BANDERAS ---
                bandera_magica = ""
                
                # 1. Buscamos primero en el tesoro robado de la competencia usando el título completo
                titulo_busqueda = titulo_completo.lower()
                
                # Búsqueda más relajada: si una parte del título completo (ej. los equipos) está en la clave del diccionario
                for clave_texto, url_logo in diccionario_banderas.items():
                     if (home_team.lower() in clave_texto and away_team.lower() in clave_texto) or (titulo_busqueda in clave_texto) or (clave_texto in titulo_busqueda):
                        bandera_magica = url_logo
                        break
                        
                # 2. Si no lo encontramos ahí, usamos tu cerebro seguro local
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

            if link:
                canal_nombre = f"Opción ({idioma})"
                if "stream=" in link:
                    canal_raw = link.split("stream=")[-1].replace("_", " ").upper()
                    canal_nombre = f"{canal_raw} ({idioma})"
                
                url_limpia = desencriptar_enlace(link)
                url_segura = url_limpia.replace("\\/", "/").replace("canales.php", "canal.php")
                
                partidos_agrupados[match_key]["servers"].append({
                    "name": canal_nombre,
                    "url": url_segura
                })
        
        partidos_extraidos = list(partidos_agrupados.values())
        partidos_extraidos.sort(key=lambda x: x["datetime"])
        
        for i, p in enumerate(partidos_extraidos):
            p["id"] = i + 1
            print(f"  -> {p['league']}: {p['homeTeam']} | {len(p['servers'])} links")
            
        return partidos_extraidos
    except Exception as e:
        print(f"[X] ERROR al procesar la API: {e}")
        return None

def actualizar_nube(datos):
    if not datos:
        print("[!] No hay datos para subir. La agenda está vacía.")
        datos = []
        
    try:
        # 1. Guardamos el archivo localmente
        with open('agenda.json', 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=4)
        print("[+] Archivo agenda.json guardado localmente.")
        
        # 2. Subimos el archivo a GitHub usando la API REST (Sin Git instalado)
        print("[*] Conectando con GitHub API...")
        
        # === CONFIGURACIÓN GITHUB ===
        github_token = "TU_NUEVO_TOKEN_AQUI" # ⚠️ RECUERDA PONER TU NUEVO TOKEN, NO EL EXPUESTO
        repo = "mesias010194/bot-futbol-libre"
        file_path = "agenda.json"
        url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # a) Leer el contenido actual y pasarlo a base64
        with open('agenda.json', 'rb') as file:
            content = file.read()
            encoded_content = base64.b64encode(content).decode('utf-8')
            
        # b) Obtener el 'sha' (identificador) del archivo anterior en GitHub para poder sobreescribirlo
        get_res = requests.get(url, headers=headers)
        sha = ""
        if get_res.status_code == 200:
            sha = get_res.json()['sha']
            
        # c) Preparar el envío
        data = {
            "message": "Actualización automática de agenda 🔄",
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            data["sha"] = sha
            
        # d) Subir el archivo
        put_res = requests.put(url, headers=headers, data=json.dumps(data))
        
        if put_res.status_code in [200, 201]:
             print("[+] ¡ÉXITO! Agenda publicada en GitHub directamente.")
        else:
             print(f"[X] Error al subir a GitHub: {put_res.status_code} - {put_res.text}")
             
    except Exception as e:
        print(f"[X] Error general al guardar/subir el archivo: {e}")

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
        
    print(f"\n[*] Escaneo y guardado finalizado a las {datetime.now().strftime('%H:%M:%S')}.")
    # Se eliminó el bucle while True, ctypes y time.sleep()
