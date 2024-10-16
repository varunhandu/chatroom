from flask import Flask, render_template, request, url_for, redirect, session
from flask_socketio import SocketIO, join_room, leave_room, send
import random
from os import path
from string import ascii_uppercase
from models import db, Message, Chatroom

DB_NAME = 'chatroom.db'

app = Flask(__name__)
app.config['SECRET_KEY'] = 'abba dabba doo'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
db.init_app(app)
socketio = SocketIO(app)

with app.app_context():
        if not path.exists(DB_NAME):
            db.create_all()
            print("DB created")

rooms = {}
# a dictionary to keep track of all active room
# consists of total number of members (int)

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
            rooms[room] = {"members" : 0}
        elif room not in rooms:
            return render_template('home.html', error='Enter a valid room code')
        
        session['room'] = room
        session['name'] = username
        chatroom_new = Chatroom(room_code=room)
        db.session.add(chatroom_new)
        db.session.commit()
        print(f"created a new room : {room}")
        return redirect(url_for('room'))

    return render_template('home.html')

@app.route('/room', methods=['GET', 'POST'])
def room():
    room = session.get('room')
    if room is None or session.get('name') is None or room not in rooms:
        return redirect(url_for('home'))
    room_instance = Chatroom.query.filter_by(room_code=room).first()
    return render_template('room.html', code=room, chatroom=room_instance)

@socketio.on('message')
def message(data):
    room = session.get('room')
    if room not in rooms:
        return
    room_instance = Chatroom.query.filter_by(room_code=room).first()
    chat = Message(sender_name=session.get('name'), content=data['data'], room_id=room_instance.id)
    db.session.add(chat)
    db.session.commit()
    msg_body = {
        'name' : session.get('name'),
        'message' : data['data'],
        'time' : chat.time
    }
    send(msg_body, to=room)
    print(f"{msg_body['name']} said {msg_body['message']} at {msg_body['time']}")

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
    room_instance = Chatroom.query.filter_by(room_code=room).first()
    join_notification = Message(sender_name=name, content='has entered the room', room_id=room_instance.id)
    db.session.add(join_notification)
    db.session.commit()
    send({'name': name, 'message': 'has entered the room', 'time' : join_notification.time}, to=room)
    print(f"{name} has joined room {room} at {join_notification.time}")
    rooms[room]['members'] +=1

@socketio.on('disconnect')
def disconnect():
    room = session.get('room')
    name = session.get('name')

    leave_room(room)
    room_instance = Chatroom.query.filter_by(room_code=room).first()

    if room in rooms:
        rooms[room]['members'] -= 1
        if rooms[room]['members'] <= 0:
            del rooms[room]
            messages = Message.query.filter_by(room_id=room_instance.id).all()
            print("deleting the following messages")
            for message in messages:
                print("->" + message.content)
                db.session.delete(message)
            db.session.delete(room_instance)
    
    leave_notification = Message(sender_name=name, content='has left the room', room_id=room_instance.id)
    db.session.add(leave_notification)
    db.session.commit()
    print(f"{name} has left room {room} at {leave_notification.time}")
    send({'name': name, 'message': 'has left the room', 'time': leave_notification.time}, to=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)