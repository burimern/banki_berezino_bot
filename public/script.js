document.getElementById('setWebhookBtn').addEventListener('click', () => {
    const statusEl = document.getElementById('status');
    statusEl.textContent = 'Устанавливаю...';

    fetch('/api/set_webhook')
        .then(response => response.text())
        .then(data => {
            statusEl.textContent = `✅ ${data}`;
            statusEl.style.color = '#03dac6';
        })
        .catch(error => {
            console.error('Ошибка:', error);
            statusEl.textContent = '❌ Произошла ошибка.';
            statusEl.style.color = '#cf6679';
        });
});
