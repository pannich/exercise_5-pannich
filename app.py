import logging
import string
import traceback
import random
import sqlite3
from datetime import datetime
from flask import * # Flask, g, redirect, render_template, request, url_for
from functools import wraps

app = Flask(__name__)

# These should make it so your Flask app always returns the latest version of
# your HTML, CSS, and JS files. We would remove them from a production deploy,
# but don't change them here.
app.debug = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache"
    return response

def get_db():
    db = getattr(g, '_database', None)

    if db is None:
        db = g._database = sqlite3.connect('db/watchparty.sqlite3')
        db.row_factory = sqlite3.Row
        setattr(g, '_database', db)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    db = get_db()
    cursor = db.execute(query, args)
    print("query_db")
    # print(cursor)
    rows = cursor.fetchall()
    # print(rows)
    db.commit()
    cursor.close()
    if rows:
        if one:
            return rows[0]
        return rows
    return None

def new_user():
    name = "Unnamed User #" + ''.join(random.choices(string.digits, k=6))
    password = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    api_key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=40))
    u = query_db('insert into users (name, password, api_key) ' +
        'values (?, ?, ?) returning id, name, password, api_key',
        (name, password, api_key),
        one=True)
    return u

def get_user_from_cookie(request):
    """_summary_
    # request.cookies is a dict
    # ie. ImmutableMultiDict([('user_id', '5'), ('user_password', '4hsq2jk0sk')])
    Args:
        request (_type_): post request
    Returns:
        user object: a sqlite row object of that user
    """
    user_id = request.cookies.get('user_id')
    password = request.cookies.get('user_password')
    if user_id and password:
        return query_db('select * from users where id = ? and password = ?', [user_id, password], one=True)
    return None

def render_with_error_handling(template, **kwargs):
    try:
        return render_template(template, **kwargs)
    except:
        t = traceback.format_exc()
        return render_template('error.html', args={"trace": t}), 500

# Authenticate USER API
def require_api_key(f):
    """a decorator function to check user api key
    Check if the requested API header 'X-API-Key' matches with current user html cookie.
    """
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        user = get_user_from_cookie(request)
        print(api_key, user, user['api_key'])
        if api_key and api_key == user['api_key']:
            return f(*args, **kwargs)
        else:
            abort(401)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ------------------------------ NORMAL PAGE ROUTES ----------------------------------

@app.route('/')
def index():
    print("index") # For debugging
    user = get_user_from_cookie(request)

    if user:
        rooms = query_db('select * from rooms')
        return render_with_error_handling('index.html', user=user, rooms=rooms)

    return render_with_error_handling('index.html', user=None, rooms=None)

@app.route('/rooms/new', methods=['GET', 'POST'])
def create_room():
    print("create room") # For debugging
    user = get_user_from_cookie(request)
    if user is None: return {}, 403

    if (request.method == 'POST'):
        name = "Unnamed Room " + ''.join(random.choices(string.digits, k=6))
        room = query_db('insert into rooms (name) values (?) returning id', [name], one=True)
        return redirect(f'{room["id"]}')
    else:
        return app.send_static_file('create_room.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("signup")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/profile')
        # return render_with_error_handling('profile.html', user=user) # redirect('/')

    if request.method == 'POST':
        u = new_user()
        print("u")
        print(u)
        for key in u.keys():
            print(f'{key}: {u[key]}')

        resp = redirect('/profile')
        resp.set_cookie('user_id', str(u['id']))
        resp.set_cookie('user_password', u['password'])
        return resp

    return redirect('/login')

@app.route('/profile')
def profile():
    print("profile")
    user = get_user_from_cookie(request)
    if user:
        return render_with_error_handling('profile.html', user=user)

    redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    print("login")
    user = get_user_from_cookie(request)

    if user:
        return redirect('/')

    if request.method == 'POST':
        name = request.form['name']
        password = request.form['name']
        u = query_db('select * from users where name = ? and password = ?', [name, password], one=True)
        if user:
            resp = make_response(redirect("/"))
            resp.set_cookie('user_id', u.id)
            resp.set_cookie('user_password', u.password)
            return resp

    return render_with_error_handling('login.html', failed=True)

@app.route('/logout')
def logout():
    resp = make_response(redirect('/'))
    resp.set_cookie('user_id', '')
    resp.set_cookie('user_password', '')
    return resp

@app.route('/rooms/<int:room_id>')
def room(room_id):
    user = get_user_from_cookie(request)
    if user is None: return redirect('/')

    room = query_db('select * from rooms where id = ?', [room_id], one=True)
    return render_with_error_handling('room.html',
            room=room, user=user)

# -------------------------------- API ROUTES ----------------------------------

# POST to change the user's name
@app.route('/api/user/name', methods=['POST'])
@require_api_key
def update_username():
    user = get_user_from_cookie(request)
    if not user: return jsonify({'error': 'User not found'}), 403

    # get new name
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            new_user_name = data.get('user_name')
        try:
            new_user = query_db('''
        UPDATE users
        SET name = ?
        WHERE id = ? RETURNING *
        ''', (new_user_name, user['id']), one=True)
            return jsonify({'message': f"Username: {new_user['name']} updated successfully"}), 200
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

# POST to change the user's password
@app.route('/api/user/password', methods=['POST'])
@require_api_key
def update_password():
    user = get_user_from_cookie(request)
    if not user: return jsonify({'error': 'User not found'}), 403

    # get new password
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            new_password = data.get('password')
        try:
            new_user = query_db('''
        UPDATE users
        SET password = ?
        WHERE id = ? RETURNING *
        ''', (new_password, user['id']), one=True)
            return jsonify({'message': f"Password: {new_user['password']} updated successfully"}), 200
        except Exception as e:
            return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

# POST to change the name of a room
@app.route('/api/rooms/changename', methods=['POST'])
@require_api_key
def change_room_name():
    """
    json request:
    room_id
    new_room_name

    Returns:
        _type_: _description_
    """
    if request.is_json:
        data = request.get_json()
        room_id = data.get('room_id')
        new_room_name = data.get('new_room_name')
    # Add your database logic here to update the room name
    try:
        query_db('''
        UPDATE rooms
        SET name = ?
        WHERE id = ?
        ''', (new_room_name, room_id), one=True)
        return jsonify({'message': 'Room name updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Internal Server Error', 'details': str(e)}), 500

# GET to get all the messages in a room
@app.route('/api/messages', methods=['GET'])
@require_api_key
def get_messages():
    room_id = request.args.get('room_id')  # Assuming you pass room_id as a query parameter
    if not room_id:
        return jsonify({'error': 'Room ID is required'}), 400

    try:
        messages = query_db('select * from messages where room_id = ?', [room_id], one=False)
        if not messages:
            return jsonify({'message': 'no message found'}), 200
        ls_messages = []
        for message in messages:
            user = get_user_from_id(message['user_id'])
            if not user:
                print("user id not found")
                continue
            ls_messages.append({'id': message['id'], 'user_name': user['name'], 'body': message['body']})
        return jsonify(ls_messages), 200
    except Exception as e:
        return jsonify({'error': f'An error occurred while fetching messages: {e}'}), 500

# POST to post a new message to a room
@app.route('/api/messages/post', methods=['POST'])
@require_api_key
def post_message():
    print("post message")
    if request.is_json:
        data = request.get_json()
        body = data.get('body')
        room_id = data.get('room_id')
        user_id = data.get('user_id')

    if not room_id:
        return jsonify({'error': 'Room ID is required'}), 400

    user = get_user_from_id(user_id)

    message = query_db('''
    INSERT INTO messages (user_id, room_id, body)
    VALUES (?, ?, ?) RETURNING user_id, room_id, body
    ''', (user_id, room_id, body), one=True)

    try:
        return jsonify({'user_name': user['name'], 'body': message['body']}), 200
    except Exception as e:
        # Log the exception e
        return jsonify({'error': 'An error occurred while fetching messages'}), 500

def get_user_from_id(user_id):
    """return user object
    """
    return query_db('select * from users where id = ?', [user_id], one=True)
