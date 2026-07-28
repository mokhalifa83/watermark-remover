const API_URL = 'https://watermark-remover.mokhalifa83.workers.dev/api';

document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('url-input');
    const removeBtn = document.getElementById('remove-btn');
    const errorMessage = document.getElementById('error-message');
    const resultContainer = document.getElementById('result-container');
    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');
    const btnText = removeBtn.querySelector('.btn-text');
    const loader = removeBtn.querySelector('.loader');

    removeBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) {
            showError('Please enter a valid Meta AI video URL');
            return;
        }
        showError('');
        resultContainer.classList.add('hidden');
        setLoading(true);

        try {
            const response = await fetch(API_URL + '/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });
            const data = await response.json();
            if (!response.ok || data.error) throw new Error(data.error || 'Failed to process video');
            showResult(data.video_url);
        } catch (error) {
            showError(error.message);
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        if (isLoading) {
            removeBtn.disabled = true;
            btnText.textContent = 'Processing...';
            loader.classList.remove('hidden');
        } else {
            removeBtn.disabled = false;
            btnText.textContent = 'Remove Watermark';
            loader.classList.add('hidden');
        }
    }

    function showError(message) {
        errorMessage.textContent = message;
        if (message) errorMessage.classList.remove('hidden');
        else errorMessage.classList.add('hidden');
    }

    function showResult(videoUrl) {
        resultContainer.classList.remove('hidden');
        urlInput.parentElement.classList.add('hidden');

        const proxyUrl = API_URL + '/proxy?url=' + encodeURIComponent(videoUrl) + '&filename=video_no_watermark.mp4';
        downloadBtn.href = proxyUrl;
        downloadBtn.setAttribute('download', 'video_no_watermark.mp4');

        const videoWrapper = resultContainer.querySelector('.video-wrapper');
        videoWrapper.innerHTML = `
            <video controls width="100%" style="border-radius: 8px; background: #000;" autoplay
                src="${proxyUrl}" 
                onerror="this.parentElement.innerHTML += '<p style=\'color: #ff4d4d; margin-top: 10px;\'>Error loading video. The link may have expired. Try again.</p>'">
                Your browser does not support the video tag.
            </video>
        `;
    }

    resetBtn.addEventListener('click', () => {
        resultContainer.classList.add('hidden');
        urlInput.value = '';
        urlInput.parentElement.classList.remove('hidden');
        const videoWrapper = resultContainer.querySelector('.video-wrapper');
        videoWrapper.innerHTML = '';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    const faqQuestions = document.querySelectorAll('.faq-question');
    faqQuestions.forEach(question => {
        question.addEventListener('click', () => {
            const item = question.parentElement;
            const isActive = item.classList.contains('active');
            document.querySelectorAll('.faq-item').forEach(otherItem => {
                otherItem.classList.remove('active');
                const otherAnswer = otherItem.querySelector('.faq-answer');
                if (otherAnswer) otherAnswer.style.maxHeight = null;
            });
            if (!isActive) {
                item.classList.add('active');
                const answer = item.querySelector('.faq-answer');
                if (answer) answer.style.maxHeight = answer.scrollHeight + 'px';
            }
        });
    });

    const statNumbers = document.querySelectorAll('.stat-number[data-count]');
    const animateCount = (element) => {
        const target = parseInt(element.getAttribute('data-count'));
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;
        const updateCount = () => {
            current += increment;
            if (current < target) {
                element.textContent = Math.floor(current).toLocaleString();
                requestAnimationFrame(updateCount);
            } else {
                element.textContent = target.toLocaleString();
            }
        };
        updateCount();
    };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCount(entry.target);
                observer.unobserve(entry.target);
            }
        });
    });
    statNumbers.forEach(stat => observer.observe(stat));
});
