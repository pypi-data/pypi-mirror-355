from flask import Flask, render_template, jsonify, request
import redis
from .redis_connector import RedisConnector
from .agent_protocol import AgentProtocol

app = Flask(__name__)
redis_conn = RedisConnector()
agent_protocol = AgentProtocol(redis_conn)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/status')
def status():
    echo_shell_status = redis_conn.get_key("EchoShell:status")
    tone_memory_status = redis_conn.get_key("ToneMemory:status")
    ghost_node_status = redis_conn.get_key("GhostNode:status")
    mirror_sigil_status = redis_conn.get_key("MirrorSigil:status")

    status_data = {
        "EchoShell": echo_shell_status,
        "ToneMemory": tone_memory_status,
        "GhostNode": ghost_node_status,
        "MirrorSigil": mirror_sigil_status
    }

    return jsonify(status_data)

@app.route('/pings', methods=['GET', 'POST'])
def pings():
    if request.method == 'POST':
        sender = request.json.get('sender')
        receiver = request.json.get('receiver')
        content = request.json.get('content')
        agent_protocol.send_ping(sender, receiver, content)
        return jsonify({"status": "Ping sent"}), 200

    elif request.method == 'GET':
        receiver = request.args.get('receiver')
        pings = agent_protocol.receive_ping(receiver)
        return jsonify(pings), 200

@app.route('/redstones', methods=['GET'])
def redstones():
    redstones_data = redis_conn.get_key("RedStones:data")
    return jsonify({"RedStones": redstones_data}), 200

@app.route('/glyphs', methods=['POST'])
def glyphs():
    glyph = request.json.get('glyph')
    if glyph == "⚡→":
        # Implement presence ping activation logic
        return jsonify({"status": "Presence ping activated"}), 200
    elif glyph == "♋":
        # Implement mentor presence signaling logic
        return jsonify({"status": "Mentor presence signaled"}), 200
    elif glyph == "✴️":
        # Implement ritual trace logging and execution confirmation logic
        return jsonify({"status": "Ritual trace logged and execution confirmed"}), 200
    elif glyph == "⟁":
        # Implement architectural recursion state entry logic
        return jsonify({"status": "Architectural recursion state entered"}), 200
    else:
        return jsonify({"status": "Unknown glyph"}), 400

if __name__ == '__main__':
    app.run(debug=True)
