const BASE_URL = window.location.href;
let selectedPiece = null;

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

function convertPosition(pos) {
	const letters = "abcdefgh";
	let col = letters.indexOf(pos[0]);
	let row = Number(pos[1]) - 1;
	return {column: col, row: row};
}

function getPosition(e) {
	let id = null;
	// Check if it's a piece or a tile
	if (e.hasClass("piece")) {
		id = e.parent().attr("id");
	} else if (e.hasClass("board_tile")) {
		id = e.attr("id");
	} else {
		return {row: -1, column: -1}
	}
	// Return the position of the tile
	return convertPosition(id.slice(id.length - 2));
}

function get(params, path) {
	let post_options = {
		method: "GET",
		body: JSON.stringify(params)
	};

// Post to the API
	return fetch(BASE_URL + path, post_options)
		// Jsonify the result
		.then(r => r.json());
}

function post(params, path) {
	let post_options = {
		method: "POST",
		body: JSON.stringify(params)
	};

// Post to the API
	return fetch(BASE_URL + path, post_options)
		// Jsonify the result
		.then(r => r.json());
}

function restart() {
	let action = "first"
	let firstPlayer = $("#first_player");
	console.log(firstPlayer.attr("checked"))
	if (firstPlayer.attr("checked") !== "checked") {
		action = "second";
	}
	post({player_choice: action}, "api/new-game")
		.then(() => window.location.reload());
}

function makeMove(piece, position) {
	post(
		{
			piece: piece,
			position: position
		},
		"api/make-move"
	).then(r => {
		if (r.type === "error") {
			// Log error
			console.log(r.message);
		} else {
			// Refresh the page
			window.location.reload();
		}
	})
}

function makeJump(piece, position, end_turn) {
	post(
		{
			piece: piece,
			position: position,
			end_turn: end_turn
		},
		"api/make-jump"
	).then(r => {
		if (r.type === "error") {
			// Log error
			console.log(r.message);
		} else {
			// Refresh the page
			window.location.reload();
		}
	})
}

function selectPiece(piece) {
	if (piece.hasClass("player_piece")) {
		// Update global piece
		if (selectedPiece != null) {
			if (selectedPiece.hasClass("king_piece"))
				selectedPiece.css({border: ".2rem solid gold"});
			else
				selectedPiece.css({border: "none"});
		}
		selectedPiece = piece;
		piece.css({border: ".2rem solid white"});
	} else {
		// Trying to select an ai piece
		if (selectedPiece != null) {
			let aiPos = getPosition(piece);
			let pos = getPosition(selectedPiece);
			// Try to jump this piece
			if (Math.abs(pos.row - aiPos.row) === 1) {
				makeJump(pos, aiPos, false);
			}
		}
	}
}

function selectTile(tile) {
	// See if a piece is already selected
	if (selectedPiece != null) {
		let id = tile.attr("id");
		let pos = convertPosition(id.slice(id.length - 2));

		// See if a piece already exists on this tile
		let children = tile.children();
		// No pieces on this tile
		if (children.length === 0) {
			let piecePos = getPosition(selectedPiece);
			// See if the tile is next to it
			if (Math.abs(piecePos.row - pos.row) === 1) {
				makeMove(piecePos, pos);
			}
		} else {
			let piecePos = getPosition(selectedPiece);
			// See if the tile is next to it
			if (Math.abs(piecePos.row - pos.row) === 1) {
				makeJump(piecePos, pos, false);
			}
		}
	}
}

function getMoves(piece) {
	get(piece, "api/available-moves").then(r => {
		console.log(r)
	})
}

getMoves({
	row: 2,
	column: 2,
})

// Get all pieces
let pieces = $(".piece");

// Register onclick handlers
pieces.each((index, piece) => {
	piece.onclick = () => selectPiece($(piece));
});

// Get all tiles
let tiles = $(".board_tile.black");

// Register onclick handlers
tiles.each((index, tile) => {
	tile.onclick = () => selectTile($(tile));
});

// Register the restart button
const restartBtn = $("#restart");
restartBtn.on("click", restart);