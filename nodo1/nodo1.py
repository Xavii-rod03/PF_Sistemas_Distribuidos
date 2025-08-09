# nodo1/nodo1.py
from flask import Flask, request, send_file, jsonify, render_template
import os, requests, threading, time

NOMBRE_NODO = "nodo1"
PUERTO = 5001
FRAGMENTOS_DIR = "fragmentos"
API_GESTION = "http://127.0.0.1:5000"


VALID_EXT = (".mp4", ".part", ".bin")

app = Flask(__name__, template_folder="templates")

# Index 
@app.route("/")
def index():
    return render_template("index.html")

# Lista de fraxmentos 
@app.route("/lista_fragmentos", methods=["GET"])
def lista_fragmentos():
    try:
        files = sorted([f for f in os.listdir(FRAGMENTOS_DIR) if f.lower().endswith(VALID_EXT)])
    except FileNotFoundError:
        files = []
    return jsonify(files)


@app.route("/fragmento/<nombre>", methods=["GET"])
def obtener_fragmento(nombre):
    path = os.path.join(FRAGMENTOS_DIR, nombre)
    if os.path.exists(path):
        return send_file(path)
    return "Fragmento no encontrado", 404


@app.route("/nuevo_fragmento", methods=["POST"])
def nuevo_fragmento():
    data = request.get_json(silent=True) or {}
    origen_nodo = data.get("nodo")
    fragmento = data.get("fragmento")
    origen_url = data.get("origen") 
    print(f"[{NOMBRE_NODO}] Notificación recibida: {fragmento} de {origen_nodo} (origen={origen_url})")
    if fragmento:
        
        if origen_url:
            intentar_descarga(origen_url, fragmento)
        else:
            buscar_y_descargar(fragmento)
    return jsonify({"status": "ok"})


def mis_fragmentos():
    os.makedirs(FRAGMENTOS_DIR, exist_ok=True)
    return sorted([f for f in os.listdir(FRAGMENTOS_DIR) if f.lower().endswith(VALID_EXT)])

def registrar_en_api():
    frags = mis_fragmentos()
    payload = {"nodo": NOMBRE_NODO, "url": f"http://127.0.0.1:{PUERTO}", "fragmentos": ",".join(frags)}
    try:
        requests.post(f"{API_GESTION}/registrar", json=payload, timeout=3)
        print(f"[{NOMBRE_NODO}] Registrado en API con {len(frags)} fragmentos.")
    except Exception as e:
        print(f"[{NOMBRE_NODO}] Error registrando en API: {e}")

def suscribirme_api():
    try:
        requests.post(f"{API_GESTION}/suscribirse", json={"url": f"http://127.0.0.1:{PUERTO}"}, timeout=3)
        print(f"[{NOMBRE_NODO}] Suscrito a notificaciones en API.")
    except Exception as e:
        print(f"[{NOMBRE_NODO}] Error suscribiendo a API: {e}")

def intentar_descarga(origen_url, nombre):
    
    try:
        r = requests.get(f"{origen_url.rstrip('/')}/fragmento/{nombre}", timeout=5)
        if r.status_code == 200:
            with open(os.path.join(FRAGMENTOS_DIR, nombre), "wb") as f:
                f.write(r.content)
            print(f"[{NOMBRE_NODO}] Descargado {nombre} desde {origen_url}")
            
            registrar_en_api()
            return True
    except Exception as e:
        print(f"[{NOMBRE_NODO}] Error descargando desde {origen_url}: {e}")
    return False

def buscar_y_descargar(nombre):
    
    try:
        resp = requests.get(f"{API_GESTION}/nodos", timeout=4)
        if resp.status_code != 200:
            return False
        data = resp.json()
        for nodo, info in data.items():
            if nodo == NOMBRE_NODO:
                continue
            if nombre in info.get("fragmentos", []):
                origen_url = info.get("url")
                return intentar_descarga(origen_url, nombre)
    except Exception as e:
        print(f"[{NOMBRE_NODO}] Error buscando fragmento en API: {e}")
    return False


def ciclo_chequeo_faltantes():
    while True:
        try:
           
            resp = requests.get(f"{API_GESTION}/nodos", timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                locales = set(mis_fragmentos())
                for nodo, info in data.items():
                    if nodo == NOMBRE_NODO:
                        continue
                    for frag in info.get("fragmentos", []):
                        if frag not in locales:
                            print(f"[{NOMBRE_NODO}] (poll) descargando {frag} desde {info.get('url')}")
                            intentar_descarga(info.get("url"), frag)
                            locales = set(mis_fragmentos())
            time.sleep(6)
        except Exception as e:
           
            time.sleep(6)

if __name__ == "__main__":
    os.makedirs(FRAGMENTOS_DIR, exist_ok=True)
    registrar_en_api()
    suscribirme_api()

    
    t = threading.Thread(target=ciclo_chequeo_faltantes, daemon=True)
    t.start()

    # 3) arrancar servidor
    print(f"[{NOMBRE_NODO}] Servidor corriendo en http://127.0.0.1:{PUERTO}")
    app.run(port=PUERTO)
