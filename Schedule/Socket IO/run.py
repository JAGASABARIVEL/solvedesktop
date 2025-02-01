from app import create_app
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

app, socketio = create_app()

if __name__ == '__main__':
    #socketio.run(app, port=5001, debug=False)
    http_server = WSGIServer(("0.0.0.0", 5001), app, handler_class=WebSocketHandler)
    http_server.serve_forever()