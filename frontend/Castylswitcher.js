const { createApp } = Vue;

        createApp({
            methods: {
                goToAuth() {
                    // Простой переход на authpage.html
                    window.location.href = 'authpage.html';
                }
            }
        }).mount('#app');