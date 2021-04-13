// General websocket errors
const Channel = {
	Move: "move",
	Jump: "Jump",
	MoveError: "move_error",
	PieceError: "piece_error",
	TurnError: "turn_error",
	Error: "error"
};

// Gets a cookie
const getCookie = (cookieKey) => {
	let cookieName = `${cookieKey}=`;
	let cookieArray = document.cookie.split(';');
	for (let cookie of cookieArray) {
		while (cookie.charAt(0) === ' ') {
			cookie = cookie.substring(1, cookie.length);
		}
		if (cookie.indexOf(cookieName) === 0) {
			return cookie.substring(cookieName.length, cookie.length);
		}
	}
}

let socket = io("/ws");

// General error handling
socket.on(Channel.Error, error => {
	// Just print the error
	console.log(error);
});

// Problem placing a move
socket.on(Channel.MoveError, error => {
	console.log(error);
});

socket.emit(
	Channel.Move,
	{
		token: getCookie("token"),
		game_id: 1,
		piece: {
			column: 0,
			row: 2,
		},
		position: {
			column: 1,
			row: 3,
		}
	}
);