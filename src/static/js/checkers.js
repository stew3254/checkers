const BASE_URL = window.location.href;
let selected_piece = null;

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
		if (selected_piece != null)
			selected_piece.css({border: "none"});
		selected_piece = piece;
		piece.css({border: ".4rem solid white"});
	} else {
		if (selected_piece != null) {
			let id = piece.parent().attr("id");
			let ai_pos = convertPosition(id.slice(id.length - 2));
			id = selected_piece.parent().attr("id")
			let pos = convertPosition(id.slice(id.length - 2));
			// Try to jump this piece
			if (Math.abs(pos.row - ai_pos.row) === 1) {
				makeJump(pos, ai_pos, false);
			}
		}
	}
}

// Get all pieces
let pieces = $(".piece");

// Register onclick handlers
pieces.each((index, piece) => {
	piece.onclick = () => selectPiece($(piece));
});
