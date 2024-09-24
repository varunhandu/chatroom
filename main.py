from flask import Flask, render_template, request, url_for, redirect, session
from flask_socketio import SocketIO, join_room, leave_room, send
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abba dabba doo'
socketio = SocketIO(app)

rooms = {}
# a dictionary to keep track of all active room
# consists of members (int) and messages (list)

def generate_code():
    code = ""
    while True:
        for _ in range(4):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code

@app.route('/', methods=['GET', 'POST'])
def home():
    session.clear()
    if request.method == 'POST':
        username = request.form.get('username')
        room_code = request.form.get('roomcode').upper()
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        if not username:
            return render_template('home.html', error='Enter your username') 
        if join != False and not room_code:
            return render_template('home.html', error='Enter the room code')

        room = room_code
        if create != False:
            room = generate_code()
            rooms[room] = {"members" : 0, "messages" : []}
            print(f"created a new room {room} with 0 members")
        elif room not in rooms:
            return render_template('home.html', error='Enter a valid room code')
        
        session['room'] = room
        session['name'] = username
        return redirect(url_for('room'))

    return render_template('home.html')

@app.route('/room', methods=['GET', 'POST'])
def room():
    room = session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('home'))
    return render_template('room.html', code=room, messages=rooms[room]["messages"])

@socketio.on('message')
def message(data):
    room = session.get('room')
    if room not in rooms:
        return
    msg_body = {
        'name' : session.get('name'),
        'message' : data['data']
    }
    send(msg_body, to=room)
    rooms[room]['messages'].append(msg_body)
    print(f"{msg_body['name']} said {msg_body['message']}")

@socketio.on('connect')
def connect(auth):
    room = session.get('room')
    name = session.get('name')

    if not room or not name:
        return

    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({'name': name, 'message': 'has entered the room' }, to=room)
    print(f"{name} has joined room {room}")
    rooms[room]['members'] +=1

@socketio.on('disconnect')
def disconnect():
    room = session.get('room')
    name = session.get('name')

    leave_room(room)
    print(f"{name} has left room {room}")

    if room in rooms:
        rooms['members'] -= 1
        if rooms['members'] <= 0:
            del rooms[room]
    
    send({'name': name, 'message': 'has left the room'}, to=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)