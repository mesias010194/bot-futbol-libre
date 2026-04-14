import requests
import json
from datetime import datetime, timedelta, timezone
import re
import time

# ==========================================================
# 1. CONFIGURACIÓN DE TU NUBE (JSONBIN.IO)
# ==========================================================
BIN_ID = "69d933e5aaba882197e5950b" 
API_KEY = "$2a$10$fH2AVYqUAGOQm6KLrAcdk.fsTBsZPp7sTDWydhhsWtaYfrLlnAWv."

# ==========================================================
# 2. EL LINK DE LA BÓVEDA SECRETA (LA14HD)
# ==========================================================
TIMESTAMP = int(time.time() * 1000)
API_ORIGEN = f"https://la14hd.com//eventos/json/agenda123.json?_={TIMESTAMP}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# ==========================================================
# 3. EL CEREBRO DE BANDERAS
# ==========================================================
def obtener_bandera(liga, encuentro):
    """ Lee el nombre de la liga o equipos y asigna una bandera automáticamente """
    texto = (liga + " " + encuentro).lower()
    
    # Países Principales
    if "perú" in texto or "liga 1" in texto or "peruano" in texto: return "https://flagcdn.com/w40/pe.png"
    if "argentina" in texto or "liga profesional" in texto or "copa de la liga" in texto: return "https://flagcdn.com/w40/ar.png"
    if "españa" in texto or "laliga" in texto or "copa del rey" in texto: return "https://flagcdn.com/w40/es.png"
    if "inglaterra" in texto or "premier" in texto or "championship" in texto or "fa cup" in texto: return "https://flagcdn.com/w40/gb-eng.png"
    if "italia" in texto or "serie a" in texto: return "https://flagcdn.com/w40/it.png"
    if "alemania" in texto or "bundesliga" in texto: return "https://flagcdn.com/w40/de.png"
    if "francia" in texto or "ligue 1" in texto: return "https://flagcdn.com/w40/fr.png"
    if "mexic" in texto or "liga mx" in texto: return "https://flagcdn.com/w40/mx.png"
    if "colombia" in texto or "betplay" in texto or "primera a" in texto: return "https://flagcdn.com/w40/co.png"
    if "chile" in texto or "campeonato nacional" in texto: return "https://flagcdn.com/w40/cl.png"
    if "uruguay" in texto: return "https://flagcdn.com/w40/uy.png"
    if "ecuador" in texto or "ligapro" in texto: return "https://flagcdn.com/w40/ec.png"
    if "brasil" in texto or "brasileirão" in texto or "paulista" in texto: return "https://flagcdn.com/w40/br.png"
    if "usa" in texto or "mls" in texto or "estados unidos" in texto: return "https://flagcdn.com/w40/us.png"
    if "arabia" in texto or "pro league" in texto: return "https://flagcdn.com/w40/sa.png"
    
    # Torneos Internacionales
    if "champions league" in texto or "uefa" in texto: return "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bf/UEFA_Champions_League_logo_2.svg/40px-UEFA_Champions_League_logo_2.svg.png"
    if "libertadores" in texto: return "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Copa_Libertadores_logo.svg/40px-Copa_Libertadores_logo.svg.png"
    if "sudamericana" in texto: return "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Copa_Sudamericana_logo.svg/40px-Copa_Sudamericana_logo.svg.png"
    if "concacaf" in texto: return "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/CONCACAF_logo.svg/40px-CONCACAF_logo.svg.png"
    if "fifa" in texto or "mundial" in texto: return "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/FIFA_logo_without_slogan.svg/40px-FIFA_logo_without_slogan.svg.png"
    
    # Pelota genérica por defecto
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Soccerball.svg/40px-Soccerball.svg.png"

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
    print(f"[*] Conectando a la API de la14hd: {API_ORIGEN[:45]}...")
    try:
        respuesta = requests.get(API_ORIGEN, headers=HEADERS, timeout=15)
        respuesta.raise_for_status() 
        datos_json = respuesta.json()
        
        partidos_agrupados = {}
        
        for item in datos_json:
            titulo_completo = item.get("title", "Partido en Vivo")
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
                
                # AQUI ACTIVAMOS EL CEREBRO DE BANDERAS
                bandera_magica = obtener_bandera(liga, encuentro)
                
                # ---- NUEVO: MENSAJE DE DIAGNÓSTICO EN CONSOLA ----
                print(f"✅ {liga}: {encuentro}")
                print(f"   -> URL de Bandera Asignada: {bandera_magica}")
                # ---------------------------------------------------
                
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
                    
                url_segura = link.replace("\\/", "/").replace("canales.php", "canal.php")
                    
                partidos_agrupados[match_key]["servers"].append({
                    "name": canal_nombre,
                    "url": url_segura
                })

        partidos_extraidos = list(partidos_agrupados.values())
        partidos_extraidos.sort(key=lambda x: x["datetime"])
            
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
            print(f"[+] ¡ÉXITO! Nube actualizada. Se agruparon y ordenaron {len(datos)} partidos.")
        else:
            print(f"[X] Error de JSONBin: {res.text}")
    except Exception as e:
        print(f"[X] Error de red: {e}")

if __name__ == "__main__":
    print("===================================================================")
    print("   BOT CAZADOR Y AGRUPADOR MÁXIMO (CON BANDERAS INTELIGENTES)      ")
    print("===================================================================")
    
    datos = extraer_partidos()
    if datos is not None: 
        actualizar_nube(datos)
