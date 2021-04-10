// General websocket errors
const Channel = {
	Move: "move",
	Jump: "Jump",
	MoveError: "move_error",
	Error: "error"
};

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
		piece: {
			column: 0,
			row: 0,
			king: false,
		},
		tile: {
			column: 1,
			row: 1,
		}
	}
);