import requests
import json
import base64
from datetime import datetime, timedelta, timezone
import re

# ==========================================================
# 1. CONFIGURACIÓN DE TU NUBE (JSONBIN.IO)
# ==========================================================
BIN_ID = "69d933e5aaba882197e5950b" 
API_KEY = "$2a$10$fH2AVYqUAGOQm6KLrAcdk.fsTBsZPp7sTDWydhhsWtaYfrLlnAWv."

# ==========================================================
# 2. EL LINK DE LA BÓVEDA SECRETA (FUBOLAZO)
# ==========================================================
API_ORIGEN = "https://fubolazo.com/agenda.json"
BASE_DOMAIN = "https://futbollibreplay.pe" 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)",
    "Accept": "application/json",
}

def desencriptar_enlace(iframe_str):
    """ Desencripta la URL de Base64 de la API de Strapi """
    try:
        if 'r=' in iframe_str:
            b64_texto = iframe_str.split('r=')[1].split('&')[0]
            url_real = base64.b64decode(b64_texto).decode('utf-8')
            return url_real
    except Exception as e:
        pass
    return iframe_str

def convertir_hora(fecha_str, hora_str):
    """ Junta la fecha y hora de la API y la convierte a UTC """
    try:
        fecha_hora_texto = f"{fecha_str} {hora_str}"
        fecha_obj = datetime.strptime(fecha_hora_texto, "%Y-%m-%d %H:%M:%S")
        
        # Asumimos que la API entrega horas de Perú/Colombia (UTC-5)
        tz_origen = timezone(timedelta(hours=-5))
        fecha_obj = fecha_obj.replace(tzinfo=tz_origen)
        
        return fecha_obj.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def extraer_partidos():
    print(f"[*] Conectando a la API: {API_ORIGEN}...")
    try:
        respuesta = requests.get(API_ORIGEN, headers=HEADERS, timeout=15)
        respuesta.raise_for_status() 
        datos_json = respuesta.json()
        
        lista_partidos = datos_json if isinstance(datos_json, list) else datos_json.get("data", [])
        
        partidos_extraidos = []
        contador_id = 1
        
        for item in lista_partidos:
            attrs = item.get("attributes", {})
            if not attrs:
                continue
                
            # Extraer Fechas y Horas
            fecha = attrs.get("date_diary", "")
            hora = attrs.get("diary_hour", "")
            datetime_utc = convertir_hora(fecha, hora)
            
            # Extraer Títulos y Equipos
            descripcion = attrs.get("diary_description", "Fútbol")
            liga = "Fútbol"
            encuentro = descripcion
            
            if ":" in descripcion:
                partes = descripcion.split(":", 1)
                liga = partes[0].strip()
                encuentro = partes[1].strip()
                
            home_team = encuentro
            away_team = ""
            if " vs " in encuentro.lower():
                equipos = re.split(r'\s+vs\s+', encuentro, flags=re.IGNORECASE)
                home_team = equipos[0].strip()
                away_team = equipos[1].strip()

            # Extraer Bandera
            bandera_url = ""
            try:
                ruta_img = attrs["country"]["data"]["attributes"]["image"]["data"]["attributes"]["url"]
                if ruta_img:
                    bandera_url = ruta_img if ruta_img.startswith("http") else BASE_DOMAIN + ruta_img
            except:
                pass

            # Extraer y Desencriptar Servidores
            servidores_extraidos = []
            lista_embeds = attrs.get("embeds", {}).get("data", [])
            
            for emb in lista_embeds:
                emb_attrs = emb.get("attributes", {})
                nombre = emb_attrs.get("embed_name", "Opción")
                iframe_encriptado = emb_attrs.get("embed_iframe", "")
                
                url_limpia = desencriptar_enlace(iframe_encriptado)
                
                if url_limpia and url_limpia.startswith("http"):
                    servidores_extraidos.append({
                        "name": nombre,
                        "url": url_limpia
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
            
        # ==========================================================
        # LA MAGIA DEL ORDEN: Acomodar por hora (de mañana a noche)
        # ==========================================================
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
            print(f"[+] ¡ÉXITO! Nube actualizada. Se subieron {len(datos)} partidos ORDENADOS.")
        else:
            print(f"[X] Error de JSONBin: {res.text}")
    except Exception as e:
        print(f"[X] Error de red: {e}")

if __name__ == "__main__":
    print("===================================================================")
    print("   BOT CAZADOR - DESENCRIPTADOR Y ORDENADOR                        ")
    print("===================================================================")
    
    datos = extraer_partidos()
    if datos is not None: 
        actualizar_nube(datos)
