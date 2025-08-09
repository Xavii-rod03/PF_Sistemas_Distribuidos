
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)


nodos_info = {}
suscriptores = set() 

def notificar_suscriptores(origen_nodo, fragmento):
  
    origen_url = nodos_info.get(origen_nodo, {}).get("url", "")
    payload = {"nodo": origen_nodo, "fragmento": fragmento, "origen": origen_url}
    for sub in list(suscriptores):
        try:
            requests.post(f"{sub}/nuevo_fragmento", json=payload, timeout=3)
            print(f"[API] Notificado a {sub} sobre {fragmento} de {origen_nodo}")
        except Exception as e:
            print(f"[API] Error notificando a {sub}: {e}")

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "mensaje": "API de gestión P2P funcionando",
        "endpoints": ["/registrar","/nodos","/fragmentos/<nodo>","/suscribirse","/suscriptores"]
    })

@app.route("/registrar", methods=["POST"])
def registrar():
    
    data = request.get_json(silent=True) or request.form
    nodo = data.get("nodo")
    url = data.get("url")
    frags = data.get("fragmentos", "")

    if not nodo or not url:
        return jsonify({"error": "Falta 'nodo' o 'url'"}), 400

    frag_list = [f.strip() for f in frags.split(",")] if frags else []
    frag_map = {f: "" for f in frag_list}  

    
    prev = set(nodos_info.get(nodo, {}).get("fragmentos", {}).keys())
    nuevos = [f for f in frag_list if f not in prev]

    nodos_info[nodo] = {"url": url.rstrip("/"), "fragmentos": frag_map}
    print(f"[API] Nodo registrado: {nodo} -> {url} ({len(frag_map)} fragmentos)")

   
    for f in nuevos:
        notificar_suscriptores(nodo, f)

    return jsonify({"status": "ok"})

@app.route("/nodos", methods=["GET"])
def listar_nodos():
    out = {}
    for n, info in nodos_info.items():
        out[n] = {"url": info.get("url", ""), "fragmentos": list(info.get("fragmentos", {}).keys())}
    return jsonify(out)

@app.route("/fragmentos/<nodo>", methods=["GET"])
def listar_fragmentos(nodo):
    if nodo not in nodos_info:
        return jsonify([]) 
    return jsonify(list(nodos_info[nodo]["fragmentos"].keys()))

@app.route("/suscribirse", methods=["POST"])
def suscribirse():
    """
    Suscribirse: { "url": "http://127.0.0.1:5001" }
    """
    data = request.get_json(silent=True) or request.form
    url = data.get("url")
    if not url:
        return jsonify({"error": "Falta 'url'"}), 400
    suscriptores.add(url.rstrip("/"))
    print(f"[API] Suscriptor agregado: {url}")
    return jsonify({"status": "suscrito"})

@app.route("/suscriptores", methods=["GET"])
def ver_suscriptores():
    return jsonify(list(suscriptores))

if __name__ == "__main__":
    print("[API] Iniciando API de gestión en http://127.0.0.1:5000")
    app.run(port=5000)
