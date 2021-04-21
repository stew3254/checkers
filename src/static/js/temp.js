params = {
	token: getCookie("token"),
		game_id: 1,
	piece: {
		row: 3,
		column: 1,
},
	position: {
		row: 4,
		column: 2,
	}
};

post_options = {
	method: "POST",
	body: JSON.stringify(params)
}

// Post to the API
fetch(BASE_URL + "api/make-jump", post_options)
	// Jsonify the result
	.then(r => r.json())
	// Actually do something with the result
	.then(r => console.log(r));