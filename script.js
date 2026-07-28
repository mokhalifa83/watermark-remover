const CORS_PROXY = 'https://api.allorigins.win/raw?url=';

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
            const proxyUrl = CORS_PROXY + encodeURIComponent(url);
            const response = await fetch(proxyUrl);
            if (!response.ok) throw new Error('Failed to fetch page: ' + response.status);
            const text = await response.text();

            const videoUrl = extractVideoUrl(text);
            if (!videoUrl) throw new Error('Could not find a video in this link. Make sure it is a direct Meta AI video post URL.');
            showResult(videoUrl);
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

        downloadBtn.href = videoUrl;
        downloadBtn.setAttribute('download', 'video_no_watermark.mp4');

        const videoWrapper = resultContainer.querySelector('.video-wrapper');
        videoWrapper.innerHTML = `
            <video controls width="100%" style="border-radius: 8px; background: #000;" autoplay
                src="${videoUrl}" 
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

function extractVideoUrl(html) {
    const mp4Regex = /https:\/\/[^\s<>"']+\.mp4(?:\?[^\s<>"']*)?/g;
    const candidates = [];
    const seen = {};
    let match;

    while ((match = mp4Regex.exec(html)) !== null) {
        let clean = match[0]
            .replace(/\\u0026/g, '&')
            .replace(/&amp;/g, '&')
            .replace(/\\\//g, '/');
        const oeMatch = clean.match(/oe=[a-fA-F0-9]{8}/);
        if (oeMatch) clean = clean.substring(0, oeMatch.index + oeMatch[0].length);
        const lt = clean.indexOf('<');
        if (lt !== -1) clean = clean.substring(0, lt);
        if (seen[clean]) continue;
        seen[clean] = true;

        const efgMatch = clean.match(/efg=([^&]+)/);
        if (!efgMatch) continue;

        try {
            const efgEncoded = efgMatch[1];
            const efgDecoded = decodeURIComponent(efgEncoded);
            const padding = (4 - (efgDecoded.length % 4)) % 4;
            const efg = JSON.parse(atob(efgDecoded + '='.repeat(padding)));
            const tag = efg.vencode_tag || efg.encoding_tag || '';
            if (tag.indexOf('progressive') !== -1) {
                const resMatch = tag.match(/(\d+)p/);
                const res = resMatch ? parseInt(resMatch[1], 10) : 0;
                candidates.push({ url: clean, resolution: res, tag: tag });
            }
        } catch (e) {}
    }

    let bestUrl = null, bestRes = 0;
    for (const c of candidates) {
        if (c.tag.indexOf('progressive') !== -1 && c.resolution > bestRes) {
            bestRes = c.resolution;
            bestUrl = c.url;
        }
    }
    return bestUrl;
}
