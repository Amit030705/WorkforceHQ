const form = document.querySelector('#login-form');
const errorBox = document.querySelector('#error-message');
const button = document.querySelector('#submit-button');

form.addEventListener('submit', async (event) => {
	event.preventDefault();
	errorBox.hidden = true;
	button.disabled = true;
	button.textContent = 'Signing in…';
	try {
		const values = new FormData(form);
		const response = await fetch('/api/v1/auth/login', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ email: values.get('email'), password: values.get('password') }),
		});
		const result = await response.json();
		if (!response.ok) throw new Error(readableError(result.detail));
		window.location.assign('/');
	} catch (error) {
		errorBox.textContent = error.message || 'Unable to sign in. Please try again.';
		errorBox.hidden = false;
		button.disabled = false;
		button.innerHTML = 'Sign in <span>→</span>';
	}
});

function readableError(detail) {
	if (typeof detail === 'string') return detail;
	if (Array.isArray(detail)) return detail.map((item) => item.msg).join(' ');
	return 'Unable to sign in. Please try again.';
}

fetch('/api/v1/auth/me').then((response) => {
	if (response.ok) window.location.replace('/');
}).catch(() => {});

