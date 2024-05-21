const socket = io();

let gameStartTime = null;
let previousGames = [];
let gameInterval = null;
let roleCheckHistory = [];

document.getElementById('startGame').addEventListener('click', () => {
    const password = document.getElementById('hostPassword').value.trim();
    if (password !== '7520') {
        alert('잘못된 암호입니다.');
        return;
    }

    const players = document.getElementById('players').value.split(',').map(p => p.trim());
    const roles = {
        'Merlin': parseInt(document.getElementById('merlinCount').value),
        'Percival': parseInt(document.getElementById('percivalCount').value),
        'Citizen': parseInt(document.getElementById('citizenCount').value),
        'Assassin': parseInt(document.getElementById('assassinCount').value),
        'Minion': parseInt(document.getElementById('minionCount').value),
        'Morgana': parseInt(document.getElementById('morganaCount').value),
        'Mordred': parseInt(document.getElementById('mordredCount').value),
        'Oberon': parseInt(document.getElementById('oberonCount').value)
    };
    socket.emit('setGame', { players, roles });
});

document.getElementById('resetGame').addEventListener('click', () => {
    const password = document.getElementById('hostPassword').value.trim();
    if (password !== '7520') {
        alert('잘못된 암호입니다.');
        return;
    }
    socket.emit('resetGame');
});

document.getElementById('showResults').addEventListener('click', () => {
    const password = document.getElementById('hostPassword').value.trim();
    if (password !== '7520') {
        alert('잘못된 암호입니다.');
        return;
    }
    const winner = document.querySelector('input[name="winner"]:checked').value;
    socket.emit('getResults', { winner });
});

document.getElementById('getRole').addEventListener('click', () => {
    const playerName = document.getElementById('playerName').value.trim();
    socket.emit('getRole', { name: playerName });
});

socket.on('roleInfo', (data) => {
    const roleElement = document.createElement('span');
    roleElement.innerText = data.role;
    roleElement.style.color = ['멀린', '퍼시벌', '시민'].includes(data.role) ? 'blue' : 'red';
    roleElement.style.fontWeight = 'bold';

    const infoElement = document.createElement('div');
    infoElement.innerText = data.info;

    const roleInfoContainer = document.getElementById('roleInfo');
    roleInfoContainer.innerHTML = '';
    roleInfoContainer.appendChild(document.createTextNode('당신의 역할은: '));
    roleInfoContainer.appendChild(roleElement);
    roleInfoContainer.appendChild(document.createElement('br'));
    roleInfoContainer.appendChild(document.createTextNode('정보: '));
    roleInfoContainer.appendChild(infoElement);
});

socket.on('updateRoleCheckHistory', (data) => {
    roleCheckHistory = data;
    updateRoleCheckHistory();
});

socket.on('gameReset', () => {
    clearInterval(gameInterval);
    document.getElementById('roleInfo').innerText = '';
    document.getElementById('players').value = '';
    document.getElementById('playerName').value = '';
    document.getElementById('resultsInfo').innerText = '진행 중인 게임이 없습니다.';
    document.getElementById('playerGameStatus').innerText = '진행 중인 게임이 없습니다.';
    document.getElementById('resultsGameStatus').innerText = '진행 중인 게임이 없습니다.';
    roleCheckHistory = [];
    updateRoleCheckHistory();
    updateGameStatus([]);
    updateHostButtonState();
});

socket.on('resultsInfo', (data) => {
    if (Object.keys(data).length === 0) {
        clearInterval(gameInterval);
        document.getElementById('resultsInfo').innerText = '진행 중인 게임이 없습니다.';
        document.getElementById('playerGameStatus').innerText = '진행 중인 게임이 없습니다.';
        document.getElementById('resultsGameStatus').innerText = '진행 중인 게임이 없습니다.';
        document.getElementById('roleInfo').innerText = '게임이 종료되었습니다.';
        return;
    }

    const winner = data.winner;
    const goodPlayers = data.players.filter(player => ['Merlin', 'Percival', 'Citizen'].includes(player.role)).map(player => player.name);
    const evilPlayers = data.players.filter(player => ['Assassin', 'Minion', 'Morgana', 'Mordred', 'Oberon'].includes(player.role)).map(player => player.name);

    const formattedGoodPlayers = goodPlayers.map(name => `<span class="good${winner === 'good' ? ' bold' : ''}">${name}</span>`).join(', ');
    const formattedEvilPlayers = evilPlayers.map(name => `<span class="evil${winner === 'evil' ? ' bold' : ''}">${name}</span>`).join(', ');

    const formattedTime = formatDate(gameStartTime);
    const resultsText = `${formattedTime} : ${formattedGoodPlayers}, ${formattedEvilPlayers}`;
    previousGames.push(resultsText);

    updatePreviousGames();
    gameStartTime = null;
    clearInterval(gameInterval);
    document.getElementById('playerGameStatus').innerText = '진행 중인 게임이 없습니다.';
    document.getElementById('resultsGameStatus').innerText = '진행 중인 게임이 없습니다.';
    document.getElementById('roleInfo').innerText = '게임이 종료되었습니다.';
    updateHostButtonState();
});

socket.on('gameStarted', () => {
    document.getElementById('playerGameStatus').innerText = '게임 진행 중...';
    document.getElementById('resultsInfo').innerText = '게임 진행 중...';
    document.getElementById('resultsGameStatus').innerText = '게임 진행 중...';
    startGameTimer();
});

socket.on('updateGameStatus', (data) => {
    gameStartTime = data.game_start_time ? new Date(data.game_start_time) : null;
    updateGameStatus(data.players);
    if (data.game_start_time) {
        startGameTimer(data.players);
    }
});

function translateRole(role) {
    const roleTranslations = {
        'Merlin': '멀린',
        'Percival': '퍼시벌',
        'Citizen': '시민',
        'Assassin': '암살자',
        'Minion': '미니언',
        'Morgana': '모르가나',
        'Mordred': '모드레드',
        'Oberon': '오베론'
    };
    return roleTranslations.get(role, role);
}

function formatDate(date) {
    const yy = String(date.getFullYear()).slice(-2);
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    const hh = String(date.getHours()).padStart(2, '0');
    const min = String(date.getMinutes()).padStart(2, '0');
    return `${yy}년 ${mm}월 ${dd}일 ${hh}시 ${min}분`;
}

function updateGameStatus(players) {
    const gameStatusText = getGameStatusText(players);
    document.getElementById('playerGameStatus').innerText = gameStatusText;
    document.getElementById('resultsGameStatus').innerText = gameStatusText;
}

function getGameStatusText(players) {
    if (gameStartTime) {
        const now = new Date();
        const elapsed = new Date(now - gameStartTime);
        const minutes = String(elapsed.getUTCMinutes()).padStart(2, '0');
        const seconds = String(elapsed.getUTCSeconds()).padStart(2, '0');
        return `현재 ${minutes}분 ${seconds}초 동안 게임이 진행 중입니다.\n현재 플레이어: ${players.join(', ')}`;
    } else {
        return '진행 중인 게임이 없습니다.';
    }
}

function updatePreviousGames() {
    const previousGamesElement = document.getElementById('previousGames');
    previousGamesElement.innerHTML = previousGames.map(game => `<li>${game}</li>`).join('');
}

function updateRoleCheckHistory() {
    const roleCheckHistoryElement = document.getElementById('roleCheckHistory');
    roleCheckHistoryElement.innerHTML = roleCheckHistory.map(record => `<li>${record}</li>`).join('');
}

function updateHostButtonState() {
    const startGameButton = document.getElementById('startGame');
    if (gameStartTime) {
        startGameButton.disabled = true;
    } else {
        startGameButton.disabled = false;
    }
}

function startGameTimer(players) {
    clearInterval(gameInterval);
    gameInterval = setInterval(() => {
        const gameStatusText = getGameStatusText(players);
        document.getElementById('playerGameStatus').innerText = gameStatusText;
        document.getElementById('resultsGameStatus').innerText = gameStatusText;
    }, 1000);
}

// Tab functionality
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tab = button.getAttribute('data-tab');
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(tab).classList.add('active');
        button.classList.add('active');
    });
});

// Initialize the first tab as active
document.querySelector('.tab-button').click();
