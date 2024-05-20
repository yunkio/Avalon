from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from datetime import datetime
import random

app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent')

players = []
assigned_roles = {}
roles_count = {}
game_start_time = None
previous_games = []

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('setGame')
def handle_set_game(data):
    global players, assigned_roles, roles_count, game_start_time
    players = data['players']
    roles_count = data['roles']
    assigned_roles = assign_roles(players, roles_count)
    game_start_time = datetime.now()
    emit('gameStarted', broadcast=True)

@socketio.on('getRole')
def handle_get_role(data):
    player_name = data['name']
    if player_name in assigned_roles:
        role = assigned_roles[player_name]
        info = get_role_info(role, assigned_roles, player_name)
        emit('roleInfo', {'role': translate_role(role), 'info': info})
    else:
        emit('roleInfo', {'role': None, 'info': '플레이어를 찾을 수 없습니다'})

@socketio.on('resetGame')
def handle_reset_game():
    global players, assigned_roles, roles_count, game_start_time, previous_games
    if game_start_time and players:
        previous_games.append({
            'start_time': game_start_time,
            'players': [{'name': player, 'role': role} for player, role in assigned_roles.items()]
        })
    players = []
    assigned_roles = {}
    roles_count = {}
    game_start_time = None
    emit('gameReset', broadcast=True)

@socketio.on('getResults')
def handle_get_results(data):
    global assigned_roles, game_start_time
    if not assigned_roles:
        emit('resultsInfo', {})
    else:
        players = [{'name': player, 'role': role} for player, role in assigned_roles.items()]
        emit('resultsInfo', {'players': players, 'winner': data['winner']}, broadcast=True)

def assign_roles(players, roles_count):
    roles = []
    for role, count in roles_count.items():
        roles.extend([role] * count)
    random.shuffle(roles)
    return {player: role for player, role in zip(players, roles)}

def translate_role(role):
    role_translations = {
        'Merlin': '멀린',
        'Percival': '퍼시벌',
        'Citizen': '시민',
        'Assassin': '암살자',
        'Minion': '미니언',
        'Morgana': '모르가나',
        'Mordred': '모드레드',
        'Oberon': '오베론'
    }
    return role_translations.get(role, role)

def get_role_info(role, assigned_roles, player_name):
    if role == 'Merlin':
        bad_roles = [p for p, r in assigned_roles.items() if r in ['Assassin', 'Minion', 'Morgana', 'Mordred']]
        return f"당신은 이 악한 플레이어들을 알고 있습니다: {', '.join(bad_roles)}"
    elif role == 'Percival':
        merlin_morgana = [p for p, r in assigned_roles.items() if r in ['Merlin', 'Morgana']]
        return f"이 플레이어들은 멀린 또는 모르가나입니다: {', '.join(merlin_morgana)}"
    elif role == 'Citizen':
        return "당신은 평범한 시민입니다."
    elif role in ['Assassin', 'Minion', 'Morgana', 'Mordred']:
        bad_roles = [p for p, r in assigned_roles.items() if r in ['Assassin', 'Minion', 'Morgana', 'Mordred'] and p != player_name]
        return f"당신은 이 악한 플레이어들을 알고 있습니다: {', '.join(bad_roles)}"
    elif role == 'Oberon':
        return "당신은 다른 악한 플레이어들을 알지 못합니다."
    return ""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
