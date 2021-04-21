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

let params = {
	token: getCookie("token"),
		game_id: 1,
	piece: {
		row: 2,
		column: 2,
},
	position: {
		row: 3,
		column: 1,
	}
};

let post_options = {
	method: "POST",
	body: JSON.stringify(params)
}

// Post to the API
fetch(BASE_URL + "api/make-move", post_options)
	// Jsonify the result
	.then(r => r.json())
	// Actually do something with the result
	.then(r => console.log(r));