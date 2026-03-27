// main.js — students will add JavaScript here as features are built

// Video Modal for "See how it works"
(function() {
    const modal = document.getElementById('videoModal');
    const openBtn = document.getElementById('howItWorksBtn');
    const closeBtn = document.getElementById('modalCloseBtn');
    const video = document.getElementById('modalVideo');
    const videoUrl = 'https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1';

    if (!modal || !openBtn) return;

    function openModal() {
        video.src = videoUrl;
        modal.classList.add('is-open');
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        video.src = '';
        modal.classList.remove('is-open');
        document.body.style.overflow = '';
    }

    openBtn.addEventListener('click', function(e) {
        e.preventDefault();
        openModal();
    });

    closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('is-open')) {
            closeModal();
        }
    });
})();
