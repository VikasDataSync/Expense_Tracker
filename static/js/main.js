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

// Analytics charts
(function() {
    const payloadEl = document.getElementById('analytics-data');
    if (!payloadEl) return;

    let payload;
    try {
        payload = JSON.parse(payloadEl.textContent || '{}');
    } catch (err) {
        return;
    }

    renderVerticalBars('monthlyChart', payload.monthly || [], 'month', 'total', true);
    renderHorizontalBars('categoryChart', payload.category || [], 'name', 'amount');
    renderHorizontalBars('weekdayChart', payload.weekday || [], 'day', 'total');

    function renderVerticalBars(containerId, items, labelKey, valueKey, showAmount) {
        const container = document.getElementById(containerId);
        if (!container) return;
        if (!items.length) {
            container.textContent = 'No data available.';
            return;
        }

        const maxValue = Math.max(...items.map(item => Number(item[valueKey] || 0)), 1);
        const chart = document.createElement('div');
        chart.className = 'analytics-bars-vertical';

        items.forEach(item => {
            const value = Number(item[valueKey] || 0);
            const barItem = document.createElement('div');
            barItem.className = 'analytics-vertical-item';

            const bar = document.createElement('span');
            bar.className = 'analytics-vertical-fill';
            bar.style.height = `${Math.max((value / maxValue) * 100, value > 0 ? 8 : 3)}%`;

            const valueLabel = document.createElement('strong');
            valueLabel.textContent = showAmount ? formatINR(value) : `${value}`;

            const label = document.createElement('small');
            label.textContent = item[labelKey];

            barItem.appendChild(bar);
            barItem.appendChild(valueLabel);
            barItem.appendChild(label);
            chart.appendChild(barItem);
        });

        container.innerHTML = '';
        container.appendChild(chart);
    }

    function renderHorizontalBars(containerId, items, labelKey, valueKey) {
        const container = document.getElementById(containerId);
        if (!container) return;
        if (!items.length) {
            container.textContent = 'No data available.';
            return;
        }

        const maxValue = Math.max(...items.map(item => Number(item[valueKey] || 0)), 1);
        const chart = document.createElement('div');
        chart.className = 'analytics-bars-horizontal';

        items.forEach(item => {
            const value = Number(item[valueKey] || 0);
            const row = document.createElement('div');
            row.className = 'analytics-horizontal-item';

            const meta = document.createElement('div');
            meta.className = 'analytics-horizontal-meta';

            const label = document.createElement('span');
            label.textContent = item[labelKey];
            const amount = document.createElement('strong');
            amount.textContent = formatINR(value);

            meta.appendChild(label);
            meta.appendChild(amount);

            const track = document.createElement('div');
            track.className = 'analytics-horizontal-track';

            const fill = document.createElement('span');
            fill.className = 'analytics-horizontal-fill';
            fill.style.width = `${(value / maxValue) * 100}%`;
            track.appendChild(fill);

            row.appendChild(meta);
            row.appendChild(track);
            chart.appendChild(row);
        });

        container.innerHTML = '';
        container.appendChild(chart);
    }

    function formatINR(value) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 2,
        }).format(value);
    }
})();
