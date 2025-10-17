// Глобальные переменные
let currentVideoId = null;
let searchTimeout = null;
let player = null;

// Функции для работы с видео
function loadVideos(searchQuery = '') {
  const videoGrid = document.getElementById('videoGrid');
  if (!videoGrid) return;

  videoGrid.innerHTML = '<div class="loading">Загрузка видео...</div>';

  // Формируем URL с параметрами поиска
  let url = 'http://localhost:8000/api/videos/';
  if (searchQuery) {
    url += `?search=${encodeURIComponent(searchQuery)}`;
  }

  fetch(url)
    .then(response => response.json())
    .then(data => {
      videoGrid.innerHTML = '';
      
      // Обработка пагинированного ответа
      const videos = data.results || data;

      if (!videos.length) {
        const emptyMessage = document.createElement('div');
        emptyMessage.className = 'empty-message';
        emptyMessage.textContent = searchQuery ? 
          `По запросу "${searchQuery}" ничего не найдено` : 
          'Нет доступных видео';
        videoGrid.appendChild(emptyMessage);
        return;
      }

      videos.forEach(video => {
        const card = document.createElement('div');
        card.className = 'video-card';
        card.onclick = () => watchVideo(video.id);
        
        card.innerHTML = `
          <div class="video-thumbnail-large">
            📹
            <div class="video-duration">${video.duration || '00:00'}</div>
          </div>
          <div class="video-info">
            <h3 class="video-title">${highlightSearchTerm(video.title, searchQuery)}</h3>
            <p class="video-author">${video.owner?.username || 'Автор'}</p>
            <div class="video-stats">
              <span class="video-views">👁 ${formatViews(video.views_count)} просмотров</span>
              <span class="video-date">${formatDate(video.created_at)}</span>
            </div>
          </div>
        `;
        videoGrid.appendChild(card);
      });

      // Показываем результаты поиска
      updateSearchResults(searchQuery, videos.length);
    })
    .catch(error => {
      console.error('Ошибка загрузки видео:', error);
      videoGrid.innerHTML = '<div class="error-message">Не удалось загрузить видео</div>';
    });
}

function logout() {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('userId');
  location.reload(); // перезагрузка страницы
}


function highlightSearchTerm(text, searchQuery) {
  if (!searchQuery) return text;
  
  const regex = new RegExp(`(${searchQuery})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}

function updateSearchResults(query, count) {
  const searchResultsDiv = document.getElementById('search-results');
  if (!searchResultsDiv) return;

  if (query) {
    searchResultsDiv.innerHTML = `
      <div class="search-results-info">
        Найдено ${count} результат(ов) по запросу "<strong>${query}</strong>"
        <button onclick="clearSearch()" class="clear-search-btn">Очистить</button>
      </div>
    `;
    searchResultsDiv.style.display = 'block';
  } else {
    searchResultsDiv.style.display = 'none';
  }
}

function performSearch() {
  const searchInput = document.querySelector('.search-container input');
  const query = searchInput.value.trim();
  
  // Очищаем предыдущий таймаут
  if (searchTimeout) {
    clearTimeout(searchTimeout);
  }
  
  // Устанавливаем новый таймаут для избежания слишком частых запросов
  searchTimeout = setTimeout(() => {
    loadVideos(query);
    
    // Обновляем URL с параметром поиска
    const url = new URL(window.location);
    if (query) {
      url.searchParams.set('search', query);
    } else {
      url.searchParams.delete('search');
    }
    window.history.replaceState({}, '', url);
  }, 500);
}

function clearSearch() {
  const searchInput = document.querySelector('.search-container input');
  searchInput.value = '';
  loadVideos();
  
  // Очищаем URL от параметра поиска
  const url = new URL(window.location);
  url.searchParams.delete('search');
  window.history.replaceState({}, '', url);
}

function initializeSearch() {
  const searchInput = document.querySelector('.search-container input');
  if (!searchInput) return;

  // Добавляем обработчики событий для поиска
  searchInput.addEventListener('input', performSearch);
  searchInput.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      performSearch();
    }
  });

  // Проверяем URL на наличие параметра поиска при загрузке
  const urlParams = new URLSearchParams(window.location.search);
  const searchQuery = urlParams.get('search');
  if (searchQuery) {
    searchInput.value = searchQuery;
    loadVideos(searchQuery);
  }
}

// Функция для инициализации Video.js плеера
function initializeVideoPlayer() {
  if (player) {
    player.dispose();
  }

      player = videojs('video-player', {
      responsive: true,
      fluid: true,
      controls: true,
      preload: 'auto',
      playbackRates: [0.5, 0.75, 1, 1.25, 1.5, 1.75, 2],
      controlBar: {
        playToggle: true,
        currentTimeDisplay: true,
        timeDivider: true,
        durationDisplay: true,
        progressControl: true,
        volumePanel: { inline: false },
        remainingTimeDisplay: false,
        fullscreenToggle: true
      },
      plugins: {
        hotkeys: { volumeStep: 0.1, seekStep: 5, enableModifiersForNumbers: false }
      }
    });

    player.ready(function () {
      // чтобы хоткеи работали
      player.el().setAttribute('tabindex', '0');
      player.el().focus();

      // твой селектор качества
      player.controlBar.addChild('QualitySelector');

      // клик по видео = play/pause (как было)
      const videoElement = player.el().querySelector('video');
      videoElement.addEventListener('click', function () {
        if (player.paused()) player.play(); else player.pause();
      });
    });


  

  // Добавляем обработчик для паузы при клике на плеер
  player.ready(function() {
    const videoElement = player.el().querySelector('video');
    
    // Обработчик клика по видео для паузы/воспроизведения
    videoElement.addEventListener('click', function(e) {
      if (player.paused()) {
        player.play();
      } else {
        player.pause();
      }
    });

    player.controlBar.addChild('QualitySelector');
  });

  return player;
}

// Функция для добавления источников видео с разным качеством
function addVideoSources(videoData) {
  const sources = [];
  
  // Добавляем HLS источник если доступен
  if (videoData.hls_path) {
    sources.push({
      src: `http://localhost:8000/media/${videoData.hls_path}`,
      type: 'application/x-mpegURL',
      label: 'Auto',
      selected: true
    });
  }
  
  // Добавляем оригинальный файл
  if (videoData.original_file) {
    const fileExtension = videoData.original_file.split('.').pop().toLowerCase();
    let mimeType = 'video/mp4';
    
    switch(fileExtension) {
      case 'webm':
        mimeType = 'video/webm';
        break;
      case 'ogg':
        mimeType = 'video/ogg';
        break;
      case 'mov':
        mimeType = 'video/quicktime';
        break;
      case 'avi':
        mimeType = 'video/x-msvideo';
        break;
    }
    
    sources.push({
      src: `http://localhost:8000/media/${videoData.original_file}`,
      type: mimeType,
      label: '1080p',
      res: 1080
    });
  }
  
  // Если есть дополнительные качества, добавляем их
  if (videoData.qualities) {
    videoData.qualities.forEach(quality => {
      sources.push({
        src: `http://localhost:8000/media/${quality.file_path}`,
        type: 'video/mp4',
        label: quality.resolution,
        res: parseInt(quality.resolution)
      });
    });
  }
  
  return sources;
}

function loadVideoDetails(videoId) {
  fetch(`http://localhost:8000/api/videos/${videoId}/`)
    .then(response => response.json())
    .then(video => {
      // Обновляем информацию о видео
      document.getElementById('video-title').textContent = video.title;
      document.getElementById('video-views').textContent = `${formatViews(video.views_count)} просмотров`;
      document.getElementById('video-date').textContent = formatDate(video.created_at);
      document.getElementById('video-description').textContent = video.description || 'Описание не указано';
      
      // Инициализируем Video.js плеер
      const videoPlayer = initializeVideoPlayer();
      
      // Добавляем источники видео
      const sources = addVideoSources(video);
      
      // Настраиваем плеер
      videoPlayer.ready(function() {
        // Устанавливаем источники
        videoPlayer.src(sources);
        
        // Настраиваем poster (превью) если доступно
        if (video.thumbnail) {
          videoPlayer.poster(`http://localhost:8000/media/${video.thumbnail}`);
        }
        
        // Автоматически начинаем воспроизведение
        videoPlayer.play().catch(error => {
          console.log('Автовоспроизведение заблокировано:', error);
        });
      });
      
      currentVideoId = videoId;
      
      // Загружаем лайки/дизлайки
      loadRatings(videoId);

      // Загружаем комментарии
      loadComments(videoId);
      
      // Увеличиваем счетчик просмотров
      incrementViews(videoId);
    })
    .catch(error => {
      console.error('Ошибка загрузки видео:', error);
    });
}

function loadRatings(videoId) {
  fetch(`http://localhost:8000/api/videos/${videoId}/ratings/`)
    .then(response => response.json())
    .then(data => {
      const likeCount = data.filter(r => r.value === 1).length;
      const dislikeCount = data.filter(r => r.value === -1).length;
      
      document.getElementById('like-count').textContent = likeCount;
      document.getElementById('dislike-count').textContent = dislikeCount;
      
      // Проверяем, поставил ли пользователь лайк/дизлайк
      const userId = localStorage.getItem('userId');
      if (userId) {
        const userRating = data.find(r => r.user.toString() === userId);
        const likeBtn = document.getElementById('like-btn');
        const dislikeBtn = document.getElementById('dislike-btn');
        
        likeBtn.classList.remove('active');
        dislikeBtn.classList.remove('active');
        
        if (userRating) {
          if (userRating.value === 1) {
            likeBtn.classList.add('active');
          } else if (userRating.value === -1) {
            dislikeBtn.classList.add('active');
          }
        }
      }
    })
    .catch(error => {
      console.error('Ошибка загрузки рейтингов:', error);
    });
}

function loadComments(videoId) {
  const commentList = document.getElementById('comment-list');
  if (!commentList) return;

  commentList.innerHTML = '<div class="loading">Загрузка комментариев...</div>';

  fetch(`http://localhost:8000/api/videos/${videoId}/comments/`)
    .then(response => response.json())
    .then(data => {
      commentList.innerHTML = '';
      
      const comments = data.results || data;

      if (!comments.length) {
        commentList.innerHTML = '<div class="empty-message">Комментариев пока нет</div>';
        return;
      }

      comments.forEach(comment => {
        const item = document.createElement('div');
        item.className = 'comment-item';
        item.innerHTML = `
          <div class="comment-avatar">👤</div>
          <div class="comment-content">
            <div class="comment-author">${comment.user.username}</div>
            <div class="comment-text">${comment.text}</div>
            <div class="comment-date">${formatDate(comment.created_at)}</div>
          </div>
        `;
        commentList.appendChild(item);
      });
    })
    .catch(error => {
      console.error('Ошибка загрузки комментариев:', error);
      commentList.innerHTML = '<div class="error-message">Не удалось загрузить комментарии</div>';
    });
}

function incrementViews(videoId) {
  fetch(`http://localhost:8000/api/videos/${videoId}/view/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      userId: localStorage.getItem('userId')
    })
  })
  .catch(error => {
    console.error('Ошибка увеличения просмотров:', error);
  });
}

// Функции для взаимодействия с видео
function toggleLike() {
  if (!currentVideoId) return;
  
  fetch(`http://localhost:8000/api/videos/${currentVideoId}/rating/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + localStorage.getItem('accessToken'),
    },
    body: JSON.stringify({ value: 1 })
  })
    .then(response => {
      if (response.ok) {
        loadRatings(currentVideoId);
      } else {
        console.error('Не удалось поставить лайк');
      }
    })
    .catch(error => console.error('Ошибка лайка:', error));
}

function toggleDislike() {
  if (!currentVideoId) return;
  
  fetch(`http://localhost:8000/api/videos/${currentVideoId}/rating/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + localStorage.getItem('accessToken'),
    },
    body: JSON.stringify({ value: -1 })
  })
    .then(response => {
      if (response.ok) {
        loadRatings(currentVideoId);
      } else {
        console.error('Не удалось поставить дизлайк');
      }
    })
    .catch(error => console.error('Ошибка дизлайка:', error));
}

// Функции для работы с профилем
function loadUserProfile() {
  const userId = localStorage.getItem('userId');
  if (!userId) return;

  fetch(`http://localhost:8000/api/users/${userId}/`, {
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('accessToken')
    }
  })
    .then(res => res.json())
    .then(data => {
      document.getElementById('username').textContent = data.username;
      if (document.getElementById('username-input')) {
        document.getElementById('username-input').value = data.username;
      }
    })
    .catch(err => console.error('Ошибка загрузки профиля:', err));
}

// Функции для загрузки видео
function uploadVideo() {
  const form = document.getElementById('uploadForm');
  const formData = new FormData(form);

  fetch('http://localhost:8000/api/videos/', {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer ' + localStorage.getItem('accessToken')
    },
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    if (data.id || data.success) {
      alert('Видео успешно загружено');
      form.reset();
      updateCharCount();
    } else {
      alert(data.error || 'Ошибка при загрузке видео');
    }
  })
  .catch(error => {
    console.error('Ошибка при загрузке видео:', error);
    alert('Ошибка при загрузке видео');
  });
}

function watchVideo(videoId) {
  showPage('watch');
  loadVideoDetails(videoId);
}


function formatViews(views) {
  if (views >= 1000000) {
    return (views / 1000000).toFixed(1) + 'M';
  } else if (views >= 1000) {
    return (views / 1000).toFixed(1) + 'K';
  }
  return views ? views.toString() : '0';
}

function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 1) {
    return 'вчера';
  } else if (diffDays < 7) {
    return `${diffDays} дней назад`;
  } else if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} ${weeks === 1 ? 'неделю' : 'недели'} назад`;
  } else {
    const months = Math.floor(diffDays / 30);
    return `${months} ${months === 1 ? 'месяц' : 'месяца'} назад`;
  }
}

function updateCharCount() {
  const textarea = document.getElementById('description');
  const charCount = document.getElementById('charCount');
  
  if (textarea && charCount) {
    charCount.textContent = textarea.value.length;
    
    if (textarea.value.length > 2700) {
      charCount.style.color = '#e74c3c';
    } else if (textarea.value.length > 2400) {
      charCount.style.color = '#f39c12';
    } else {
      charCount.style.color = '#666';
    }
  }
}

function showPage(page) {
  const pages = ['home', 'watch', 'upload', 'profile'];
  pages.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.style.display = (id === page) ? 'block' : 'none';
    }
  });
  
  closeMenu();
  location.hash = page;
  
  // Загружаем данные для страницы
  if (page === 'home') {
    // Проверяем, есть ли поисковый запрос
    const searchInput = document.querySelector('.search-container input');
    const query = searchInput ? searchInput.value.trim() : '';
    loadVideos(query);
  } else if (page === 'profile') {
    loadUserProfile();
  }
}

function toggleMenu() {
  const hamburger = document.querySelector('.hamburger');
  const dropdown = document.getElementById('dropdownMenu');
  
  hamburger.classList.toggle('active');
  dropdown.classList.toggle('active');
}

function closeMenu() {
  const hamburger = document.querySelector('.hamburger');
  const dropdown = document.getElementById('dropdownMenu');
  
  hamburger.classList.remove('active');
  dropdown.classList.remove('active');
}

function closeModal(modalId) {
  document.getElementById(modalId).style.display = 'none';
  const inputs = document.querySelectorAll(`#${modalId} input`);
  inputs.forEach(input => input.value = '');
}

function handleHashChange() {
  const hash = location.hash.replace('#', '') || 'home';
  showPage(hash);
}

// Инициализация
function initializeApp() {
  
  handleHashChange();
  initializeSearch();

  const loginBtn = document.getElementById('login-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const isLoggedIn = !!localStorage.getItem('accessToken');

  if (isLoggedIn) {
    loginBtn.style.display = 'none';
    logoutBtn.style.display = 'inline-block';
  } else {
    loginBtn.style.display = 'inline-block';
    logoutBtn.style.display = 'none';
  }


  const commentButton = document.getElementById('submit-comment');
  if (commentButton) {
    commentButton.addEventListener('click', () => {
      const input = document.getElementById('comment-input');
      const text = input.value.trim();
      if (!text) return;

      fetch(`http://localhost:8000/api/videos/${currentVideoId}/comments/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + localStorage.getItem('accessToken')
        },
        body: JSON.stringify({
          text: text,
          video: currentVideoId
        })
      })
      .then(response => response.json())
      .then(data => {
        input.value = '';
        loadComments(currentVideoId);
      })
      .catch(error => {
        console.error('Ошибка при добавлении комментария:', error);
      });
    });
  }

  // Добавляем обработчик для формы загрузки
  const uploadForm = document.querySelector('#upload form');
  if (uploadForm) {
    uploadForm.addEventListener('submit', function(e) {
      e.preventDefault();
      uploadVideo();
    });
  }
  
  // Добавляем обработчик для счетчика символов
  const textarea = document.getElementById('description');
  if (textarea) {
    textarea.addEventListener('input', updateCharCount);
  }
}

// Обработчики событий
document.addEventListener('click', function(event) {
  const hamburger = document.querySelector('.hamburger');
  const dropdown = document.getElementById('dropdownMenu');
  
  if (hamburger && dropdown) {
    if (!hamburger.contains(event.target) && !dropdown.contains(event.target)) {
      closeMenu();
    }
  }
  
  if (event.target.classList.contains('modal')) {
    event.target.style.display = 'none';
  }
});


window.addEventListener('hashchange', handleHashChange);
window.addEventListener('load', initializeApp);