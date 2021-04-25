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

function post(params) {
	let post_options = {
		method: "POST",
		body: JSON.stringify(params)
	};

// Post to the API
	return fetch(BASE_URL + "api/make-move", post_options)
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
		}
	).then(r => {
		if (r.type === "error")
			console.log(r);
	})
}
