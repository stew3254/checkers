const BASE_URL = window.location.href;
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

function make_move(piece, position) {
	post(
		{
			token: getCookie("token"),
			game_id: getCookie("game_id"),
			piece: piece,
			position: position
		},
		"/api/make-move"
	).then(r => {
		if (r.type === "error")
			console.log(r);
	})
}

function make_jump(piece, position, end_turn) {
	post(
		{
			token: getCookie("token"),
			game_id: Number(getCookie("game_id")),
			piece: piece,
			position: position,
			end_turn: end_turn
		},
		"/api/make-jump"
	).then(r => {
		if (r.type === "error")
			console.log(r);
	})
}

make_move(
	{"row": 2, column: 2},
	{"row": 3, column: 1},
)

make_jump(
	{"row": 3, column: 1},
	{"row": 4, column: 2},
	false
)

make_jump(
	{"row": 5, column: 3},
	{"row": 6, column: 2},
	true
)
