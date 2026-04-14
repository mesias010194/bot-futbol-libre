import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone
import re

# ==========================================================
# 1. CONFIGURACIÓN DE TU NUBE (JSONBIN.IO)
# ==========================================================
BIN_ID = "69d933e5aaba882197e5950b" 
API_KEY = "$2a$10$fH2AVYqUAGOQm6KLrAcdk.fsTBsZPp7sTDWydhhsWtaYfrLlnAWv."

URL_ORIGEN = "https://www.futbolibre.pe/"
# Cabeceras mejoradas para que la página de origen no nos bloquee
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
}

MAPEO_BANDERAS = {
    "FRA": "https://flagcdn.com/w40/fr.png", "ALE": "https://flagcdn.com/w40/de.png",
    "IT": "https://flagcdn.com/w40/it.png", "ES": "https://flagcdn.com/w40/es.png",
    "ENG": "https://flagcdn.com/w40/gb-eng.png", "ARG": "https://flagcdn.com/w40/ar.png",
    "BRA": "https://flagcdn.com/w40/br.png", "URU": "https://flagcdn.com/w40/uy.png",
    "COL": "https://flagcdn.com/w40/co.png", "CHI": "https://flagcdn.com/w40/cl.png",
    "INT": "https://flagcdn.com/w40/un.png"
}

def convertir_hora_a_utc(hora_texto):
    try:
        hora_limpia = hora_texto.strip().lower().replace('hs', '').replace(' ', '')
        try:
            hora_obj = datetime.strptime(hora_limpia, "%H:%M")
        except ValueError:
            hora_obj = datetime.strptime(hora_limpia, "%I:%M%p")
        
        tz_origen = timezone(timedelta(hours=1)) # Servidor en Europa UTC+1
        ahora_origen = datetime.now(tz_origen)
        
        fecha_partido_origen = ahora_origen.replace(
            hour=hora_obj.hour, minute=hora_obj.minute, second=0, microsecond=0
        )
        fecha_utc = fecha_partido_origen.astimezone(timezone.utc)
        return fecha_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def extraer_partidos():
    print(f"[*] Escaneando {URL_ORIGEN} ...")
    try:
        respuesta = requests.get(URL_ORIGEN, headers=HEADERS, timeout=15)
        respuesta.raise_for_status() 
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        partidos_extraidos = []
        
        menu_principal = soup.find('ul', class_='menu')
        if not menu_principal: 
            print("[X] ERROR: No se encontró la lista de partidos. La página de origen pudo haber cambiado.")
            return [] # Retornamos lista vacía para que borre los partidos viejos de tu web
            
        filas_partidos = menu_principal.find_all('li', recursive=False)
        
        contador_id = 1
        for fila in filas_partidos:
            try:
                clases = fila.get('class', [])
                codigo_pais = clases[0].upper() if clases else "INT"
                url_bandera = MAPEO_BANDERAS.get(codigo_pais, MAPEO_BANDERAS["INT"])
                
                enlaces_en_fila = fila.find_all('a')
                if not enlaces_en_fila: continue
                
                enlace_principal = enlaces_en_fila[0]
                span_hora = enlace_principal.find('span', class_='t')
                hora_texto = span_hora.text.strip() if span_hora else "00:00"
                datetime_utc = convertir_hora_a_utc(hora_texto)
                
                texto_crudo = ""
                for nodo in enlace_principal.contents:
                    if isinstance(nodo, str): texto_crudo += nodo.strip() + " "
                texto_crudo = texto_crudo.strip()
                
                if not texto_crudo and span_hora:
                    texto_crudo = enlace_principal.text.replace(hora_texto, "").strip()
                
                liga = "Fútbol"
                equipos = texto_crudo
                if ":" in texto_crudo:
                    partes = texto_crudo.split(":", 1)
                    liga = partes[0].strip()
                    equipos = partes[1].strip()
                
                home_team = equipos
                away_team = ""
                if re.search(r'\s+vs\s+', equipos, re.IGNORECASE):
                    equipos_split = re.split(r'\s+vs\s+', equipos, flags=re.IGNORECASE)
                    home_team = equipos_split[0].strip()
                    away_team = equipos_split[1].strip()

                servidores_extraidos = []
                if len(enlaces_en_fila) > 1:
                    for i, op in enumerate(enlaces_en_fila[1:]):
                        url_stream = op.get('href', '#')
                        nombre_opcion = op.text.strip() or f"Opción {i+1}"
                        if url_stream and url_stream != "#":
                            servidores_extraidos.append({"name": nombre_opcion, "url": url_stream})
                
                partidos_extraidos.append({
                    "id": contador_id, "datetime": datetime_utc, "flagUrl": url_bandera,
                    "league": liga, "homeTeam": home_team, "awayTeam": away_team,
                    "servers": servidores_extraidos
                })
                contador_id += 1
            except: continue
        return partidos_extraidos
    except Exception as e:
        print(f"[X] ERROR al conectar con la página origen: {e}")
        return None

def actualizar_nube(datos):
    url_actualizacion = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
    headers = { 'Content-Type': 'application/json', 'X-Master-Key': API_KEY }
    try:
        res = requests.put(url_actualizacion, json=datos, headers=headers)
        if res.status_code == 200:
            print(f"[+] ¡ÉXITO! Nube actualizada. Se enviaron {len(datos)} partidos.")
        else:
            print(f"[X] Error de JSONBin al subir: {res.text}")
    except Exception as e:
        print(f"[X] Error de red al intentar subir a JSONBin: {e}")

if __name__ == "__main__":
    print("===================================================================")
    print("   BOT ACTUALIZADOR DEFINITIVO (VERSIÓN GITHUB ACTIONS)            ")
    print("===================================================================")
    
    # Se eliminó el "while True" y el "time.sleep".
    # GitHub ejecutará este archivo una vez cada 10 minutos automáticamente.
    datos = extraer_partidos()
    if datos is not None: 
        actualizar_nube(datos)
    
    print("[*] Ejecución finalizada correctamente.")
