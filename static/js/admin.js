// admin.js: small helpers for dashboard chart and sales filtering
function renderSalesChart(data) {
    try {
        const ctx = document.getElementById('salesChart');
        if (!ctx) return;
        const labels = data.labels || [];
        const values = data.values || [];
        new Chart(ctx, {
            type: 'line',
            data: { labels: labels, datasets: [{ label: 'Sales (₹)', data: values, backgroundColor: 'rgba(198,40,40,0.12)', borderColor: '#c62828', tension: 0.25, fill: true }] },
            options: { responsive: true, plugins: { legend: { display: false } } }
        });
    } catch (e) {
        console.error('Chart render error', e);
    }
}

function initSalesFilters() {
    const search = document.getElementById('salesSearch');
    const status = document.getElementById('salesStatus');
    const table = document.getElementById('salesTable');
    if (!table) return;
    const tbody = table.tBodies[0];

    function applyFilter() {
        const q = (search && search.value || '').toLowerCase().trim();
        const s = (status && status.value) || '';
        for (const row of tbody.rows) {
            const product = row.cells[1].textContent.toLowerCase();
            const user = row.cells[2].textContent.toLowerCase();
            const rowStatus = row.getAttribute('data-status') || '';
            let show = true;
            if (q) show = (product.includes(q) || user.includes(q));
            if (s) show = show && (rowStatus === s);
            row.style.display = show ? '' : 'none';
        }
    }

    if (search) search.addEventListener('input', applyFilter);
    if (status) status.addEventListener('change', applyFilter);
}

window.renderSalesChart = renderSalesChart;
window.initSalesFilters = initSalesFilters;

// sidebar toggle for small screens
function setupSidebarToggle() {
    const btn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('adminSidebar');
    if (!btn || !sidebar) return;
    btn.addEventListener('click', (e) => {
        e.preventDefault();
        sidebar.classList.toggle('show');
    });
    // close when clicking outside on small screens
    document.addEventListener('click', (ev) => {
        if (!sidebar.classList.contains('show')) return;
        if (!sidebar.contains(ev.target) && ev.target !== btn) {
            sidebar.classList.remove('show');
        }
    });
}

window.setupSidebarToggle = setupSidebarToggle;
document.addEventListener('DOMContentLoaded', () => { if (window.setupSidebarToggle) setupSidebarToggle(); });
