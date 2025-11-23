let currentPage = 1;
let currentQ = '';
let currentCategory = '';

async function fetchProducts(page = 1) {
    currentPage = page;
    const per_page = 12;
    const params = new URLSearchParams();
    params.set('page', page);
    params.set('per_page', per_page);
    if (currentQ) params.set('q', currentQ);
    if (currentCategory) params.set('category', currentCategory);
    const res = await fetch('/api/products?' + params.toString());
    const data = await res.json();
    renderProducts(data.products);
    renderPagination(data.total, data.page, data.per_page);
    document.getElementById('resultsInfo').textContent = `${data.total} results`;
}

function renderProducts(products) {
    const container = document.getElementById('products');
    container.innerHTML = '';
    for (const p of products) {
        const col = document.createElement('div');
        col.className = 'col-sm-6 col-md-4 col-lg-3';
        col.innerHTML = `
      <div class="card product-card h-100">
        ${p.image_url ? `<img src="${p.image_url}" class="card-img-top" alt="${p.name}">` : `<div class="placeholder-img"></div>`}
        <div class="card-body d-flex flex-column">
          <h5 class="card-title">${p.name}</h5>
          <p class="mb-1"><span class="badge bg-primary category-badge">${p.category || 'General'}</span></p>
          <p class="mt-auto"><strong>$${p.price.toFixed(2)}</strong></p>
          <a href="/product/${p.id}" class="btn btn-sm btn-primary mt-2">View</a>
        </div>
      </div>
    `;
        container.appendChild(col);
    }
}

function renderPagination(total, page, per_page) {
    const pages = Math.max(1, Math.ceil(total / per_page));
    const ul = document.getElementById('pagination');
    ul.innerHTML = '';
    for (let i = 1; i <= pages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === page ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        li.addEventListener('click', (e) => { e.preventDefault(); fetchProducts(i); });
        ul.appendChild(li);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('searchInput');
    const categorySelect = document.getElementById('categoryFilter');
    searchInput.addEventListener('input', () => { currentQ = searchInput.value; fetchProducts(1); });
    categorySelect.addEventListener('change', () => { currentCategory = categorySelect.value; fetchProducts(1); });

    // populate categories from API (simple approach: fetch all and dedupe)
    fetch('/api/products?per_page=1000').then(r => r.json()).then(data => {
        const cats = new Set(data.products.map(p => p.category).filter(Boolean));
        for (const c of cats) {
            const opt = document.createElement('option');
            opt.value = c; opt.textContent = c; categorySelect.appendChild(opt);
        }
    });

    fetchProducts(1);
});
