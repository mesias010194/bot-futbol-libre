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
# Le agregamos un contador de tiempo para evadir su caché
# ==========================================================
TIMESTAMP = int(time.time() * 1000)
API_ORIGEN = f"https://la14hd.com//eventos/json/agenda123.json?_={TIMESTAMP}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

def convertir_hora(fecha_str, hora_str):
    """ Junta la fecha y hora de la API y la convierte a UTC """
    try:
        fecha_hora_texto = f"{fecha_str} {hora_str}"
        fecha_obj = datetime.strptime(fecha_hora_texto, "%Y-%m-%d %H:%M")
        
        # Asumimos que la API entrega horas de Perú/Colombia/Ecuador (UTC-5)
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
        
        # Diccionario para agrupar los canales que pertenecen al mismo partido
        partidos_agrupados = {}
        
        for item in datos_json:
            titulo_completo = item.get("title", "Partido en Vivo")
            fecha = item.get("date", "")
            hora = item.get("time", "")
            link = item.get("link", "")
            idioma = item.get("language", "Español")
            estado = item.get("status", "")
            
            # Filtramos solo los partidos (ignoramos repeticiones u otras categorías raras si las hay)
            if not titulo_completo or "Futbol" not in item.get("category", ""):
                pass 
            
            # Clave única para agrupar: Fecha + Hora + Título
            match_key = f"{fecha}_{hora}_{titulo_completo}"
            
            # Si el partido no existe en nuestro agrupador, lo creamos
            if match_key not in partidos_agrupados:
                liga = "Fútbol"
                encuentro = titulo_completo
                
                # Separar Liga y Equipos ("Liga 1: ADT vs Alianza Lima")
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
                
                partidos_agrupados[match_key] = {
                    "datetime": datetime_utc,
                    "flagUrl": "", 
                    "league": liga,
                    "homeTeam": home_team,
                    "awayTeam": away_team,
                    "servers": []
                }
            
            # Añadir el canal a la lista de servidores del partido
            if link:
                canal_nombre = f"Opción ({idioma})"
                
                if "stream=" in link:
                    canal_raw = link.split("stream=")[-1].replace("_", " ").upper()
                    canal_nombre = f"{canal_raw} ({idioma})"
                    
                # --- TRUCO ANTI-BLOQUEO MÁXIMO ---
                # Limpiamos la URL y cambiamos 'canales.php' (protegido) por 'canal.php' (libre)
                url_segura = link.replace("\\/", "/").replace("canales.php", "canal.php")
                    
                partidos_agrupados[match_key]["servers"].append({
                    "name": canal_nombre,
                    "url": url_segura
                })

        # Convertir nuestro grupo en una lista final para la nube
        partidos_extraidos = []
        contador_id = 1
        for match_key, data in partidos_agrupados.items():
            data["id"] = contador_id
            partidos_extraidos.append(data)
            contador_id += 1
            
        # ==========================================================
        # ORDENAR LA LISTA CRONOLÓGICAMENTE (MAÑANA A NOCHE)
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
            print(f"[+] ¡ÉXITO! Nube actualizada. Se agruparon y ordenaron {len(datos)} partidos.")
        else:
            print(f"[X] Error de JSONBin: {res.text}")
    except Exception as e:
        print(f"[X] Error de red: {e}")

if __name__ == "__main__":
    print("===================================================================")
    print("   BOT CAZADOR Y AGRUPADOR MÁXIMO (VERSIÓN LA14HD)                 ")
    print("===================================================================")
    
    datos = extraer_partidos()
    if datos is not None: 
        actualizar_nube(datos)
