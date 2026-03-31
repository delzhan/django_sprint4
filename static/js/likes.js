document.addEventListener('DOMContentLoaded', function() {
    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    }

    document.querySelectorAll('.like-button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const url = this.dataset.url;
            const countSpan = this.querySelector('.like-count');
            const iconSpan = this.querySelector('.like-icon');

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                countSpan.textContent = data.likes_count;
                iconSpan.textContent = data.liked ? '❤️' : '🩶';
            })
            .catch(error => console.error('Error:', error));
        });
    });
});