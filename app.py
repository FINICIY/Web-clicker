#библиотеки
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.utils import secure_filename
import os
import json

#атрибуты переменных
app = Flask(__name__)
app.secret_key = 'ab121'

#|----------------------------------------------------|
#|                    0    0                          |
#|                    -____-                          |
#|      DREWAX; CODE BACKEND; COIN PLACE AND SN       |
#|                                                    |
#|                Ver. 0.0.0.5 state                  |
#|----------------------------------------------------|

def get_top_users(data, num_users):
    users = data.get('users', {})
    sorted_users = sorted(users.values(), key=lambda user: user['currency'], reverse=True)
    return sorted_users[:num_users]

def load_data():
    try:
        with open('data.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = {'users': {}}
    return data

def save_data(data):
    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4)

data = load_data()

@app.route('/')
def index():
    user = session.get('user', None)
    return render_template('index.html', data=data, user=user)

#КЛИК КЛИК КЛИК КЛИК КЛИК
@app.route('/click', methods=['POST'])
def click():
    if 'user' in session:
        user = session['user']
        user['currency'] += 1
        session['user'] = user
        data = load_data()
        data['users'][user['username']] = user
        save_data(data)

#Рег система
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_username = request.form.get('username')
        new_password = request.form.get('password')
        if new_username and new_password:
            if new_username not in data['users']:
                user_id = len(data['users']) + 1
                new_user = {
                    'id': user_id,
                    'username': new_username,
                    'password': new_password,
                    'currency': 0,
                    'inventory': [],
                    'avatar': '/static/avatars/user1_avatar.png',
                    'is_banned': False 
                }
                data['users'][new_username] = new_user
                save_data(data)
                flash('Registration successful! You can now log in.')
                return redirect(url_for('login'))
            else:
                flash('Username is already taken. Please choose a different username.')

    return render_template('register.html')

#Логин система
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in data['users']:
            user = data['users'][username]
            if user['is_banned']:
                flash('Your account has been banned. Please contact support for more information.')
            elif user['password'] == password:
                session['user'] = user
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password. Please try again.')
        else:
            flash('User not found.')

    return render_template('login.html')

#Редактирование пользователя
@app.route('/update_profile', methods=['POST'])
def update_profile():
    new_username = request.form.get('new_username')
    avatar = request.files['avatar']
    user = session.get('user')
    if user:
        user['username'] = new_username
        if avatar:
            filename = secure_filename(avatar.filename)
            avatar.save(os.path.join('static/avatars', filename))
            user['avatar'] = f'static/avatars/{filename}'
        data = load_data()
        data['users'][user['username']] = user
        save_data(data)

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/items')
def item_list():
    with open('items.json', 'r') as json_file:
        items = json.load(json_file)

    return render_template('items.html', items=items)

#покупка товаров (не ворк)
@app.route('/buy_item/<item_id>', methods=['POST'])
def buy_item(item_id):
    data = load_data()
    user = session.get('user', None)
    try:
        item_id = int(item_id)
    except ValueError:
        return "Invalid item ID"
    if user:
        item_id = int(item_id)
        if (
            item_id in data['items']
            and user['currency'] >= data['items'][item_id]['price']
        ):
            user['currency'] -= data['items'][item_id]['price']
            user['inventory'].append(item_id)
            data['items'][item_id]['available'] -= 1
            save_data(data)
            flash('Item purchased successfully!')
        else:
            flash('Unable to purchase the item.')

    return redirect(url_for('item_list'))
def export_items_to_json(data):
    items_data = data.get('items', {})
    output_filename = 'items.json'
    with open(output_filename, 'w') as json_file:
        json.dump(items_data, json_file, indent=4)

#хз че это
@app.route('/export_items', methods=['GET'])
def export_items():
    data = load_data()
    export_items_to_json(data)
    flash('Items data exported to items.json!')
    return redirect(url_for('item_list'))

#Профили (не рабочие)
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = session.get('user')
    if user:
        if request.method == 'POST':
            new_username = request.form.get('new_username')
            if new_username:
                user['username'] = new_username
                flash('Username updated successfully.')
            else:
                flash('Please provide a new username.', 'error')

            avatar = request.files.get('avatar')
            if avatar:
                user['avatar'] = 'path_to_new_avatar.jpg'
                flash('Avatar updated successfully.')

            return redirect(url_for('profile'))
        return render_template('profile.html', user=user)
    else:
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('login'))

#Обновление данных о пользователе
@app.route('/update_user_data', methods=['GET'])
def update_user_data():
    username = session.get('user').get('username')
    data = load_data()

    if username in data['users']:
        session['user'] = data['users'][username]
        return jsonify({'success': True, 'new_currency': session['user']['currency']})
    else:
        return jsonify({'success': False})

#система выдачи коинов
@app.route('/get_currency')
def get_currency():
    if 'user' in session:
        currency = session['user']['currency']
        return jsonify(success=True, currency=currency)
    return jsonify(success=False, message='User not logged in')

@app.route('/transfer')
def transfer():
    return render_template('transfer.html')

@app.route('/transfer', methods=['POST'])
def transfer_funds():
    if 'user' in session:
        sender = session['user']
        recipient_username = request.form.get('recipient')
        amount = int(request.form.get('amount'))

        data = load_data()

        if sender['username'] == recipient_username:
            flash('You cannot transfer funds to yourself.')
        elif recipient_username not in data['users']:
            flash('Recipient not found.')
        elif sender['currency'] < amount:
            flash('Insufficient funds.')
        else:
            recipient = data['users'][recipient_username]
            sender['currency'] -= amount
            recipient['currency'] += amount
            save_data(data)
            flash(f'Transferred {amount} coins to {recipient_username} successfully!')

    return redirect(url_for('transfer'))

@app.route('/top_users/<int:num>', methods=['GET'])
def top_users(num):
    all_users = data['users'].values()
    top_users = [user for user in all_users if not user['is_banned']]
    top_users = sorted(top_users, key=lambda user: user['currency'], reverse=True)[:num]
    return render_template('top_users.html', top_users=top_users)

#опять отрибуты flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
