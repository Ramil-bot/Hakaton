<template>
<div id="watch" style="display: none;">
        <main>
          <div class="watch-container">
            <div class="watch-layout">
              <div class="watch-main">
                <div class="video-player-container">
                  <video
                    id="video-player"
                    class="video-js vjs-default-skin"
                    controls
                    preload="auto"
                    width="100%"
                    height="400"
                    data-setup='{}'
                  >
                    <p class="vjs-no-js">
                      Для просмотра видео необходимо включить JavaScript, и рассмотрите возможность обновления до
                      <a href="https://videojs.com/html5-video-support/" target="_blank">
                        браузера, который поддерживает HTML5 видео
                      </a>.
                    </p>
                  </video>
                </div>
                <div class="video-details">
                  <h2 id="video-title">Название видео</h2>
                  <div class="video-meta">
                    <span id="video-views">0 просмотров</span>
                    <span id="video-date">Дата загрузки</span>
                  </div>
                  <div class="like-dislike-container" style="margin-top: 1rem; margin-left: auto; width: fit-content;">
                    <button id="like-btn" onclick="toggleLike()">👍 <span id="like-count">0</span></button>
                    <button id="dislike-btn" onclick="toggleDislike()">👎 <span id="dislike-count">0</span></button>
                  </div>
                </div>
                <div class="description-section">
                  <h3>Описание</h3>
                  <p id="video-description">Описание...</p>
                </div>
                <div class="comment-container">
                  <h3>Комментарии</h3>
                  <div id="comment-list" style="max-height: 250px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-bottom: 10px;"></div>
                  <div class="comment-form">
                    <textarea id="comment-input" placeholder="Напишите комментарий..." rows="3" style="width: 100%; resize: vertical;"></textarea>
                    <button id="submit-comment" type="button">Отправить</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
</template>