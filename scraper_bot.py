import requests
import json
import base64
from datetime import datetime, timedelta, timezone
import re
import time

# ==========================================================
# 1. CONFIGURACIÓN DE TU NUBE (JSONBIN.IO)
# ==========================================================
BIN_ID = "69d933e5aaba882197e5950b" 
API_KEY = "$2a$10$fH2AVYqUAGOQm6KLrAcdk.fsTBsZPp7sTDWydhhsWtaYfrLlnAWv."

# ==========================================================
# 2. LOS LINKS DE LAS BÓVEDAS (AGENDA FRESCA + FOTOS)
# ==========================================================
API_AGENDA = "https://la14hd.com/eventos/json/agenda123.json"
API_BANDERAS = "https://fubolazo.com/agenda.json"
BASE_DOMAIN_IMG = "https://img.fubolazo.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
}

# ==========================================================
# 3. CEREBRO DE BANDERAS (Respaldo por si Fubolazo falla)
# ==========================================================
def obtener_bandera(liga, encuentro):
    texto = (liga + " " + encuentro).lower()
    
    # Torneos Internacionales
    if "champions" in texto or "campeones de la uefa" in texto: return "https://cdn-icons-png.flaticon.com/512/520/520786.png"
    if "libertadores" in texto: return "https://cdn-icons-png.flaticon.com/512/1043/1043444.png"
    if "sudamericana" in texto: return "https://cdn-icons-png.flaticon.com/512/3112/3112946.png"
    if "concacaf" in texto: return "https://cdn-icons-png.flaticon.com/512/9903/9903672.png" 
    if "afc" in texto or "asia" in texto: return "https://cdn-icons-png.flaticon.com/512/6104/6104033.png"
    if "fifa" in texto or "mundial" in texto or "conmebol" in texto or "clasificatorias" in texto: return "https://cdn-icons-png.flaticon.com/512/323/323326.png"

    # Países y Ligas
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
    
    # Pelota genérica por defecto
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

def convertir_hora(fecha_str, hora_str):
    try:
        fecha_hora_texto = f"{fecha_str} {hora_str}"
        fecha_obj = datetime.strptime(fecha_hora_texto, "%Y-%m-%d %H:%M")
        tz_origen = timezone(timedelta(hours=-5))
        fecha_obj = fecha_obj.replace(tzinfo=tz_origen)
        return fecha_obj.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def extraer_partidos():
    timestamp = int(time.time() * 1000)
    
    # =================================================================
    # FASE 1: ROBAR EL DICCIONARIO DE FOTOS DE FUBOLAZO
    # =================================================================
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
            print(f"    -> Memorizadas {len(diccionario_banderas)} banderas oficiales.")
    except Exception as e:
        print(f"[!] Aviso: No se pudieron cargar las banderas oficiales ({e})")

    # =================================================================
    # FASE 2: ROBAR LA AGENDA SÚPER ACTUALIZADA DE LA14HD
    # =================================================================
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

                datetime_utc = convertir_hora(fecha, hora)
                
                # LA MAGIA: Buscar la foto en la memoria de Fubolazo, sino usar nuestro Cerebro
                bandera_magica = diccionario_banderas.get(titulo_completo.lower(), "")
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
        
        # Asignar IDs únicos y mostrar en consola
        for i, p in enumerate(partidos_extraidos):
            p["id"] = i + 1
            print(f"  -> {p['league']}: {p['homeTeam']} | B: {p['flagUrl'][:20]}... | {len(p['servers'])} links")
            
        return partidos_extraidos
    except Exception as e:
        print(f"[X] ERROR al procesar la API: {e}")
        return None

def actualizar_nube(datos):
    if not datos:
        print("[!] No hay datos para subir.")
        return
        
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
    headers = { 'Content-Type': 'application/json', 'X-Master-Key': API_KEY }
    try:
        res = requests.put(url, json=datos, headers=headers)
        if res.status_code == 200:
            print(f"[+] ¡ÉXITO! Nube actualizada con {len(datos)} partidos (Fotos Fubolazo + Agenda La14HD).")
        else:
            print(f"[X] Error de JSONBin: {res.text}")
    except Exception as e:
        print(f"[X] Error de red: {e}")

if __name__ == "__main__":
    print("===================================================================")
    print("   BOT HÍBRIDO: AGENDA LA14HD + FOTOS FUBOLAZO (CADA 10 MIN)       ")
    print("===================================================================")
    
    # BUCLE INFINITO
    while True:
        ahora = datetime.now().strftime("%H:%M:%S")
        print(f"\n--- INICIANDO ESCANEO A LAS {ahora} ---")
        
        datos = extraer_partidos()
        if datos is not None: 
            actualizar_nube(datos)
            
        print("\n[*] Escaneo finalizado. Durmiendo por 10 minutos zZz...")
        time.sleep(600)
