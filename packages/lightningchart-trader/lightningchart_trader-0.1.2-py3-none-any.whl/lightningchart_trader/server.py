from __future__ import annotations

from flask import Flask, request, render_template, send_from_directory, Response
from flask_socketio import SocketIO, join_room
import msgpack
import threading
import os
import sys

base_dir = '.'
if hasattr(sys, '_MEIPASS'):
    base_dir = os.path.join(sys._MEIPASS)

host_name = '0.0.0.0'
app = Flask(
    __name__,
    static_folder=os.path.join(base_dir, 'static'),
    template_folder=os.path.join(base_dir, 'static'),
)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='gevent', ping_timeout=60)

connected_clients = dict()
storage = dict()
preserve_data = True
license_key = None


@app.route('/resources/<path:path>')
def send_resource(path):
    return send_from_directory('./static/resources', path)


@app.route('/static/<path:path>')
def send_static_resource(path):
    return send_from_directory('./static', path)


@app.route('/setLicense', methods=['POST'])
def set_license():
    data = msgpack.unpackb(request.data)
    global license_key
    license_key = data['license']
    return '', 200


@app.route('/')
def index():
    room = request.args.get('id')
    return render_template('index.html', room=room, license_key=license_key)


@socketio.on('connect')
def connect():
    connected_clients[request.sid] = 'default'


@socketio.on('disconnect')
def handle_disconnect():
    del connected_clients[request.sid]


@socketio.on('join')
def join(room):
    join_room(room)
    connected_clients[request.sid] = room
    if room in storage:
        socketio.emit('exec', to=room)


@socketio.on('shutdown')
def shutdown():
    os._exit(0)


@app.route('/item', methods=['POST'])
def send_item():
    room = request.args.get('id')
    binary_data = request.data

    if room not in storage:
        storage[room] = []

    save = False
    if room in connected_clients.values():
        socketio.emit('item', binary_data, to=room)
    else:
        save = True

    if preserve_data or save:
        data = msgpack.unpackb(binary_data)
        storage[room].append(data)

    return '', 200


@app.route('/exec')
def execute():
    room = request.args.get('id')
    if room in connected_clients.values():
        socketio.emit('exec', to=room)
    return '', 200


@app.route('/fetch_data')
def fetch_data():
    room = request.args.get('id')
    try:
        data = msgpack.packb(storage[room])
        if not preserve_data:
            del storage[room]
        return Response(data, mimetype='application/msgpack')
    except KeyError:
        return Response('Room not found', status=404)


def start_thread(server_port: int = 5656):
    server_thread = threading.Thread(
        target=lambda: socketio.run(
            app,
            host=host_name,
            port=server_port,
            debug=True,
            log_output=False,
            use_reloader=False,
        )
    )
    server_thread.start()
