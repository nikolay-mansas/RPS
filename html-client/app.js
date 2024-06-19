document.addEventListener("DOMContentLoaded", () => {
    const SERVER_SSL = false; // Adjust based on your server configuration
    const SERVER_IP = "localhost"; // Replace with your server IP
    const SERVER_PORT = "8000"; // Replace with your server port
    const SERVER_PREFIX = "/rps"; // Replace with your server prefix

    const ws = new WebSocket(`ws${SERVER_SSL ? 's' : ''}://${SERVER_IP}:${SERVER_PORT}${SERVER_PREFIX}`);
    let username;
    let lobbyId;
    let userId;
    let go = false;

    const loginScreen = document.getElementById("login-screen");
    const lobbyScreen = document.getElementById("lobby-screen");
    const gameScreen = document.getElementById("game-screen");
    const statusMessage = document.getElementById("status-message");
    const moveButtons = document.getElementById("move-buttons");
    const moveError = document.getElementById("move-error");

    const showScreen = (screen) => {
        loginScreen.classList.add("hidden");
        lobbyScreen.classList.add("hidden");
        gameScreen.classList.add("hidden");
        screen.classList.remove("hidden");
    };

    const showError = (element, message) => {
        element.innerText = message;
    };

    document.getElementById("login-button").addEventListener("click", () => {
        username = document.getElementById("username").value;
        if (username.length >= 4) {
            ws.send(JSON.stringify({ data: { username: username } }));
        } else {
            alert("The minimum length for a name is 4 characters");
        }
    });

    document.getElementById("create-lobby-button").addEventListener("click", () => {
        ws.send(JSON.stringify({ data: { lobby_create: true } }));
    });

    document.getElementById("join-lobby-button").addEventListener("click", () => {
        const lobbyInput = document.getElementById("lobby-id-input").value.trim();
        ws.send(JSON.stringify({ data: { lobby_id: lobbyInput } }));
    });

    const submitMove = (move) => {
        ws.send(JSON.stringify({ data: { choise: move } }));
        moveButtons.classList.add("hidden");
    };

    const pollGameStatus = (move) => {
        if (go) {
            ws.send(JSON.stringify({ data: { choise: move } }));
       }
    };

    document.querySelectorAll(".move-button").forEach(button => {
        button.addEventListener("click", () => {
            if (!go) {
                const move = button.getAttribute("data-move");
                submitMove(move);
                MyMove = move;
                console.log(MyMove);
                go = true;
                setInterval(pollGameStatus, 1000, move);
            }
        });
    });

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const loginError = document.getElementById("login-error");
        const lobbyError = document.getElementById("lobby-error");

        if (data.status) {
            moveError.innerText = '';
            if (!userId) {
                userId = data.data.user_id;
                showScreen(lobbyScreen);
            }
            if (!lobbyId && data.data.lobby_id) {
                lobbyId = data.data.lobby_id;
                document.getElementById("lobby-id").innerText = lobbyId;
                showScreen(gameScreen);
            }
            if (data.data.who_win) {
                let message;
                const opponentUsername = data.data.opponent_username || "Opponent";
                if (data.data.who_win === "draw") {
                    message = `Draw! ${username} and ${opponentUsername}.`;
                } else if (data.data.who_win === userId) {
                    message = `You win against ${opponentUsername}!`;
                } else {
                    message = `You lose to ${opponentUsername}.`;
                }
                statusMessage.innerText = message;
                go = false;
            }
        } else {
            if (data.error_message) {
                if (loginError && !userId) {
                    showError(loginError, data.error_message);
                } else if (lobbyError && !lobbyId) {
                    showError(lobbyError, data.error_message);
                } else if (moveError) {
                    showError(moveError, data.error_message);
                }
            }
        }
    };
});
