function handleLogin(event) {
  event.preventDefault();
  clearErrors();

  const formData = new FormData(event.target);
  const login = formData.get('login');
  const password = formData.get('password');

  let isValid = true;

  if (!login.trim()) {
    showError('login-input', 'Поле обязательно для заполнения');
    isValid = false;
  }

  if (!password.trim() || password.length < 6) {
    showError('login-password', 'Пароль должен содержать минимум 6 символов');
    isValid = false;
  }

  if (!isValid) return;

  const submitBtn = document.getElementById('login-submit');
  submitBtn.classList.add('loading');

  fetch('http://localhost:8000/api/token/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: login, password: password })
  })
    .then(res => res.json())
    .then(data => {
      if (data.access && data.refresh) {
        localStorage.setItem('accessToken', data.access);
        localStorage.setItem('refreshToken', data.refresh);

        const payload = JSON.parse(atob(data.access.split('.')[1]));
        localStorage.setItem('userId', payload.user_id);

        window.location.href = '/';
      } else {
        showError('login-password', 'Неверные данные');
      }
    })
    .catch(err => {
      console.error('Ошибка входа:', err);
      showError('login-password', 'Сервер недоступен');
    })
    .finally(() => submitBtn.classList.remove('loading'));
}

function handleRegister(event) {
  event.preventDefault();
  clearErrors();

  const formData = new FormData(event.target);
  const username = formData.get('username');
  const email = formData.get('email');
  const phone = formData.get('phone');
  const password = formData.get('password');
  const confirmPassword = formData.get('confirmPassword');

  let isValid = true;

  // Валидация имени пользователя
  if (!username.trim()) {
    showError('register-username', 'Поле обязательно для заполнения');
    isValid = false;
  } else if (username.length < 3) {
    showError('register-username', 'Имя пользователя должно содержать минимум 3 символа');
    isValid = false;
  } else {
    showSuccess('register-username');
  }

  // Валидация email
  if (!email.trim()) {
    showError('register-email', 'Поле обязательно для заполнения');
    isValid = false;
  } else if (!validateEmail(email)) {
    showError('register-email', 'Введите корректный email адрес');
    isValid = false;
  } else {
    showSuccess('register-email');
  }



  // Валидация пароля
  const passwordReq = validatePassword(password);
  if (!password.trim()) {
    showError('register-password', 'Поле обязательно для заполнения');
    isValid = false;
  } else if (!passwordReq.length || !passwordReq.letter || !passwordReq.number) {
    showError('register-password', 'Пароль не соответствует требованиям');
    isValid = false;
  } else {
    showSuccess('register-password');
  }

  // Валидация подтверждения пароля
  if (!confirmPassword.trim()) {
    showError('register-confirm-password', 'Поле обязательно для заполнения');
    isValid = false;
  } else if (password !== confirmPassword) {
    showError('register-confirm-password', 'Пароли не совпадают');
    isValid = false;
  } else {
    showSuccess('register-confirm-password');
  }

  if (!isValid) return;

  const submitBtn = document.getElementById('register-submit');
  submitBtn.classList.add('loading');

  fetch('http://localhost:8000/api/token/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username,
      email,
      password
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert('Регистрация успешна, теперь войдите');
        switchTab('login');
      } else {
        alert('Ошибка регистрации');
        console.error(data);
      }
    })
    .catch(err => {
      console.error('Ошибка регистрации:', err);
      alert('Ошибка соединения с сервером');
    })
    .finally(() => submitBtn.classList.remove('loading'));
}