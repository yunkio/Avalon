import os
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import random
import pytz

app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent', ping_timeout=3600, ping_interval=60)

players = []
assigned_roles = {}
roles_count = {}
game_start_time = None
previous_games = []
role_check_history = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify(status='alive'), 200

@socketio.on('setGame')
def handle_set_game(data):
    global players, assigned_roles, roles_count, game_start_time, role_check_history
    players = data['players']
    roles_count = data['roles']
    assigned_roles = assign_roles(players, roles_count)
    game_start_time = datetime.now(pytz.timezone('Asia/Seoul'))
    role_check_history = []
    emit('gameStarted', broadcast=True)
    emit('updateGameStatus', {'players': players, 'game_start_time': game_start_time.isoformat()}, broadcast=True)
    emit('updateRoleCheckHistory', role_check_history, broadcast=True)

@socketio.on('getRole')
def handle_get_role(data):
    player_name = data['name']
    if player_name in assigned_roles:
        role = assigned_roles[player_name]
        info = get_role_info(role, assigned_roles, player_name)
        timestamp = datetime.now(pytz.timezone('Asia/Seoul')).strftime('%H:%M:%S')
        role_check_history.insert(0, f"[{timestamp}] {player_name}님이 역할을 확인하였습니다.")
        if len(role_check_history) > 10:
            role_check_history.pop()
        emit('roleInfo', {'role': translate_role(role), 'info': info})
        emit('updateRoleCheckHistory', role_check_history, broadcast=True)
    else:
        emit('roleInfo', {'role': None, 'info': '플레이어를 찾을 수 없습니다'})

@socketio.on('resetGame')
def handle_reset_game():
    global players, assigned_roles, roles_count, game_start_time, previous_games, role_check_history
    if game_start_time and players:
        previous_games.append({
            'start_time': game_start_time,
            'players': [{'name': player, 'role': role} for player, role in assigned_roles.items()]
        })
    players = []
    assigned_roles = {}
    roles_count = {}
    game_start_time = None
    role_check_history = []
    emit('gameReset', broadcast=True)
    emit('updateGameStatus', {'players': [], 'game_start_time': None}, broadcast=True)
    emit('updateRoleCheckHistory', role_check_history, broadcast=True)

@socketio.on('getResults')
def handle_get_results(data):
    global assigned_roles, game_start_time
    if not assigned_roles:
        emit('resultsInfo', {})
    else:
        players_roles = [{'name': player, 'role': role} for player, role in assigned_roles.items()]
        emit('resultsInfo', {'players_roles': players_roles, 'winner': data['winner']}, broadcast=True)

@socketio.on('connect')
def handle_connect():
    global players, game_start_time, role_check_history
    emit('updateGameStatus', {'players': players, 'game_start_time': game_start_time.isoformat() if game_start_time else None})
    emit('updateRoleCheckHistory', role_check_history)

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
        # 오베론을 포함한 악역 플레이어 리스트를 만듭니다. 모드레드는 제외합니다.
        bad_roles = [p for p, r in assigned_roles.items() if r in ['Assassin', 'Minion', 'Morgana', 'Oberon']]
        return f"당신은 모드레드를 제외한 이 악한 플레이어들을 알고 있습니다: {', '.join(bad_roles)}"
    elif role == 'Percival':
        merlin_morgana = [p for p, r in assigned_roles.items() if r in ['Merlin', 'Morgana']]
        return f"이 플레이어들은 멀린 또는 모르가나입니다: {', '.join(merlin_morgana)}"
    elif role == 'Citizen':
        return "당신은 평범한 시민입니다."
    elif role in ['Assassin', 'Minion', 'Morgana', 'Mordred']:
        # 오베론을 제외한 다른 악역 플레이어들을 반환합니다.
        bad_roles = [p for p, r in assigned_roles.items() if r in ['Assassin', 'Minion', 'Morgana', 'Mordred'] and p != player_name]
        return f"당신은 이 악한 플레이어들을 알고 있습니다: {', '.join(bad_roles)}"
    elif role == 'Oberon':
        return "당신은 다른 악한 플레이어들을 알지 못합니다."
    return ""


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
