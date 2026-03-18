// API Configuration - Change this once you deploy your backend
const API_CONFIG = {
    BASE_URL: window.location.origin
};

document.addEventListener('DOMContentLoaded', () => {
    // Clear storage on load to ensure no stale video URLs
    localStorage.removeItem('cachedVideoUrl');
    sessionStorage.clear();

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

        // Reset state
        showError('');
        resultContainer.classList.add('hidden');
        setLoading(true);

        try {
            // The server extracts the URL AND streams the video back in one shot.
            // We receive raw video bytes — Meta's CDN URL is used server-side only,
            // never exposed to the browser, and consumed before it can expire.
            const response = await fetch(`${API_CONFIG.BASE_URL}/api/remove-watermark`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url }),
            });

            if (!response.ok) {
                // Try to parse error JSON
                let errMsg = 'Failed to process video';
                try {
                    const errData = await response.json();
                    errMsg = errData.error || errMsg;
                } catch (_) {}
                throw new Error(errMsg);
            }

            // Convert the streamed bytes into a local Blob URL
            const blob = await response.blob();
            const blobUrl = URL.createObjectURL(blob);

            showResult(blobUrl);

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
        if (message) {
            errorMessage.classList.remove('hidden');
        } else {
            errorMessage.classList.add('hidden');
        }
    }

    function showResult(blobUrl) {
        resultContainer.classList.remove('hidden');
        urlInput.parentElement.classList.add('hidden');

        // blob: URL lives in the browser's memory — completely independent of Meta's CDN
        downloadBtn.href = blobUrl;
        downloadBtn.setAttribute('download', 'meta_ai_video_no_watermark.mp4');

        const videoWrapper = resultContainer.querySelector('.video-wrapper');
        videoWrapper.innerHTML = `
            <video controls width="100%" style="border-radius: 8px;" autoplay>
                <source src="${blobUrl}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
        `;
    }

    resetBtn.addEventListener('click', () => {
        resultContainer.classList.add('hidden');
        urlInput.value = '';
        urlInput.parentElement.classList.remove('hidden');

        // Clear video to stop playback
        const videoWrapper = resultContainer.querySelector('.video-wrapper');
        videoWrapper.innerHTML = '';
    });


    // FAQ Accordion Logic
    const faqQuestions = document.querySelectorAll('.faq-question');

    faqQuestions.forEach(question => {
        question.addEventListener('click', () => {
            const item = question.parentElement;
            const isActive = item.classList.contains('active');

            // Close all other items
            document.querySelectorAll('.faq-item').forEach(otherItem => {
                otherItem.classList.remove('active');
                const otherAnswer = otherItem.querySelector('.faq-answer');
                if (otherAnswer) otherAnswer.style.maxHeight = null;
            });

            // Toggle current item
            if (!isActive) {
                item.classList.add('active');
                const answer = item.querySelector('.faq-answer');
                if (answer) answer.style.maxHeight = answer.scrollHeight + "px";
            }
        });
    });
});


// Animated counter for stats
document.addEventListener('DOMContentLoaded', () => {
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
