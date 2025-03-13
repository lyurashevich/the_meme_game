function navigateTo(page) {
	document.querySelectorAll('.page').forEach(el => {
	el.classList.remove('active');
	});

	document.getElementById(page).classList.add('active');

	window.history.pushState({ page }, '', `?page=${page}`);
}

function changeText() {
	const greeting = document.getElementById('greeting');

	if (greeting.innerText === 'hello') {
	greeting.innerText = 'good bye';
	}
	else {
	greeting.innerText = 'hello';
	}
}

function changeBackgroundColor() {
	const randomColor = '#' + Math.floor(Math.random()*16777215).toString(16);

	document.body.style.backgroundColor = randomColor;
}
