import requests
import json
from datetime import datetime, timedelta, timezone
import re

# ==========================================================
# 1. CONFIGURACIÓN DE TU NUBE (JSONBIN.IO)
# ==========================================================
BIN_ID = "69d933e5aaba882197e5950b" 
API_KEY = "$2a$10$fH2AVYqUAGOQm6KLrAcdk.fsTBsZPp7sTDWydhhsWtaYfrLlnAWv."

# LA NUEVA "BÓVEDA SECRETA" QUE DESCUBRISTE
API_ORIGEN = "https://viper.jugacosenamas.store/categorias?android=false"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    "Accept": "application/json",
}

def convertir_hora_a_utc(hora_texto):
    try:
        hora_limpia = hora_texto.strip().lower().replace('hs', '').replace(' ', '')
        try:
            hora_obj = datetime.strptime(hora_limpia, "%H:%M")
        except ValueError:
            hora_obj = datetime.strptime(hora_limpia, "%I:%M%p")
        
        # Esta API es de Perú, por lo tanto el horario base es UTC-5
        tz_origen = timezone(timedelta(hours=-5)) 
        ahora_origen = datetime.now(tz_origen)
        
        fecha_partido_origen = ahora_origen.replace(
            hour=hora_obj.hour, minute=hora_obj.minute, second=0, microsecond=0
        )
        fecha_utc = fecha_partido_origen.astimezone(timezone.utc)
        return fecha_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def extraer_partidos():
    print(f"[*] Conectando a la Base de Datos Secreta: {API_ORIGEN} ...")
    try:
        respuesta = requests.get(API_ORIGEN, headers=HEADERS, timeout=15)
        respuesta.raise_for_status() 
        
        # Transformamos la respuesta directamente a un diccionario JSON
        datos_json = respuesta.json()
        partidos_crudos = datos_json.get("data", [])
        
        partidos_extraidos = []
        contador_id = 1
        
        for item in partidos_crudos:
            # Filtramos la sección "PRINCIPAL" que solo contiene canales de TV 24/7
            if item.get("nombre", "").upper() == "PRINCIPAL":
                continue
                
            liga = item.get("nombre", "Fútbol")
            titulo = item.get("titulo", "Partido en Vivo")
            horario = item.get("horario", "00:00")
            bandera_url = item.get("pais", "") # La API ya nos da la foto exacta
            
            datetime_utc = convertir_hora_a_utc(horario)
            
            # Separar los equipos detectando el "vs"
            home_team = titulo
            away_team = ""
            if " vs " in titulo.lower():
                equipos_split = re.split(r'\s+vs\s+', titulo, flags=re.IGNORECASE)
                home_team = equipos_split[0].strip()
                away_team = equipos_split[1].strip()

            # Extraer las opciones de canales/servidores
            servidores_extraidos = []
            for canal in item.get("canales", []):
                nombre_canal = canal.get("titulo", f"Opción")
                url_stream = canal.get("url_video", "")
                
                # Filtro de seguridad: Solo guardamos links directos reales (que empiezan con http)
                # Esto evita que pasen links falsos o relativos que romperían tu reproductor
                if url_stream and url_stream.startswith("http"):
                    servidores_extraidos.append({
                        "name": nombre_canal, 
                        "url": url_stream
                    })
            
            partidos_extraidos.append({
                "id": contador_id, 
                "datetime": datetime_utc, 
                "flagUrl": bandera_url,
                "league": liga, 
                "homeTeam": home_team, 
                "awayTeam": away_team,
                "servers": servidores_extraidos
            })
            contador_id += 1
            
        return partidos_extraidos
    except Exception as e:
        print(f"[X] ERROR al procesar la API: {e}")
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
        print(f"[X] Error de red al subir a JSONBin: {e}")

if __name__ == "__main__":
    print("===================================================================")
    print("   BOT CAZADOR DE APIs (VERSIÓN VIPER)                             ")
    print("===================================================================")
    
    datos = extraer_partidos()
    if datos is not None: 
        actualizar_nube(datos)
    
    print("[*] Ejecución finalizada.")
