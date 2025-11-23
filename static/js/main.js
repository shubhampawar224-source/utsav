let currentPage = 1;
let currentQ = '';
let currentCategory = '';
let allProducts = [];

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
    const infoElem = document.getElementById('resultsInfo');
    if (infoElem) infoElem.textContent = `${data.total} results`;
}

function renderProducts(products) {
    const container = document.getElementById('products');
    if (!container) return;
    container.innerHTML = '';
    for (const p of products) {
        // show INR when available, otherwise fall back to USD
        const displayPrice = (typeof p.price_inr !== 'undefined' && p.price_inr !== null)
            ? `₹${Number(p.price_inr).toFixed(2)}`
            : `$${Number(p.price).toFixed(2)}`;
        const col = document.createElement('div');
        col.className = 'col-sm-6 col-md-4 col-lg-3';
        col.innerHTML = `
            <div class="card product-card h-100">
                ${p.image_url ? `<div class="card-img-wrap"><img src="${p.image_url}" alt="${p.name}"></div>` : `<div class="card-img-wrap"><div class="placeholder-img"></div></div>`}
                <div class="card-body d-flex flex-column">
                    <h5 class="card-title">${p.name}</h5>
                    <div class="d-flex justify-content-between align-items-center mb-2">
                      <span class="category-badge">${p.category || 'General'}</span>
                      <span class="price-badge">${displayPrice}</span>
                    </div>
                    <a href="/product/${p.id}" class="btn btn-sm btn-primary mt-auto">View</a>
                </div>
            </div>
        `;
        container.appendChild(col);
    }
}

function renderPagination(total, page, per_page) {
    const pages = Math.max(1, Math.ceil(total / per_page));
    const ul = document.getElementById('pagination');
    if (!ul) return;
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
    if (searchInput) searchInput.addEventListener('input', () => {
        currentQ = searchInput.value;
        // filter featured items on the homepage based on search
        const filtered = allProducts.filter(p => !currentQ || p.name.toLowerCase().includes(currentQ.toLowerCase()) || (p.description || '').toLowerCase().includes(currentQ.toLowerCase()));
        renderFeatured(filtered.slice(0, 8));
    });

    // populate categories from API (simple approach: fetch all and dedupe)
    fetch('/api/products?per_page=1000').then(r => r.json()).then(data => {
        allProducts = data.products || [];
        const cats = Array.from(new Set(data.products.map(p => p.category).filter(Boolean)));
        const navList = document.getElementById('navbarCategories');
        if (navList) {
            for (const c of cats) {
                const li = document.createElement('li');
                // build link that renders category in-place instead of full navigation
                const a = document.createElement('a');
                a.className = 'dropdown-item';
                a.href = '#';
                a.textContent = c;
                a.addEventListener('click', (e) => {
                    e.preventDefault();
                    // render category view in-place and show all records immediately
                    currentCategory = c;
                    renderCategoryPage(c).then(() => {
                        // after rendering category (featured + grid), show all items
                        fetch('/api/products?per_page=1000').then(r => r.json()).then(all => {
                            const items = all.products.filter(p => p.category === c);
                            renderFeatured(items.slice(0, 8));
                            renderProducts(items);
                            const pag = document.getElementById('pagination'); if (pag) pag.innerHTML = '';
                        });
                    });
                    // update URL for bookmarking
                    try { history.pushState({}, '', '/category/' + encodeURIComponent(c)); } catch (err) { }
                });
                li.appendChild(a);
                navList.appendChild(li);
            }
        }
        // if not on a category page, render only featured on the homepage (no per-category sections)
        if (!window.location.pathname.startsWith('/category')) {
            renderFeatured(allProducts.slice(0, 8));
        } else {
            // on category page, ensure currentCategory set from global and render category-specific UI
            if (window.currentCategory) {
                currentCategory = window.currentCategory;
                renderCategoryPage(currentCategory);
            }
        }
    });

    // Open categories dropdown on hover for non-touch devices
    try {
        const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        const dropdownToggle = document.getElementById('categoriesToggle') || document.getElementById('categoriesDropdown');
        const dropdownEl = document.getElementById('navbarCategories');
        if (dropdownToggle && dropdownEl) {
            // defer to Bootstrap's Dropdown API
            const bsDropdown = bootstrap.Dropdown.getOrCreateInstance(dropdownToggle);
            const parent = dropdownToggle.closest('.dropdown');
            if (!isTouch && parent) {
                // hover behavior for desktop
                parent.addEventListener('mouseenter', () => bsDropdown.show());
                parent.addEventListener('mouseleave', () => bsDropdown.hide());
                // keyboard accessibility
                dropdownToggle.addEventListener('focus', () => bsDropdown.show());
                dropdownToggle.addEventListener('blur', () => bsDropdown.hide());
            } else {
                // touch devices or fallback: toggle on click/tap
                dropdownToggle.addEventListener('click', (e) => {
                    e.preventDefault();
                    try { bsDropdown.toggle(); } catch (err) { }
                });
            }
        }
    } catch (err) {
        // ignore if bootstrap not available or errors occur
        console.warn('Hover dropdown init failed', err);
    }
});

async function renderHomeSections() {
    // fetch all categories then render a small section for each (first 4 items)
    const all = await fetch('/api/products?per_page=1000').then(r => r.json());
    const cats = Array.from(new Set(all.products.map(p => p.category).filter(Boolean)));
    const sections = document.getElementById('sections');
    if (!sections) return;
    sections.innerHTML = '';
    // render featured at top
    renderFeatured(all.products.slice(0, 8));
    for (const c of cats) {
        // apply search filter if present
        const items = all.products.filter(p => p.category === c && (!currentQ || p.name.toLowerCase().includes(currentQ.toLowerCase()) || (p.description || '').toLowerCase().includes(currentQ.toLowerCase()))).slice(0, 4);
        if (items.length === 0) continue;
        const sec = document.createElement('div');
        sec.className = 'mb-4';
        sec.innerHTML = `
            <div class="d-flex justify-content-between mb-2 align-items-center">
                <h5>${c}</h5>
                <a href="/category/${encodeURIComponent(c)}">View all</a>
            </div>
            <div class="row g-3">
                ${items.map(p => `
                    <div class="col-6 col-md-3">
                            <div class="card h-100 product-card">
                            <div class="card-img-wrap"><img src="${p.image_url}" alt="${p.name}"></div>
                            <div class="card-body d-flex flex-column">
                                <h6 class="card-title">${p.name}</h6>
                                <div class="d-flex justify-content-between align-items-center mt-auto">
                                  <span class="price-badge">${(typeof p.price_inr !== 'undefined' && p.price_inr !== null) ? '₹' + Number(p.price_inr).toFixed(2) : '$' + Number(p.price).toFixed(2)}</span>
                                  <a class="btn btn-sm btn-primary" href="/product/${p.id}">View</a>
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        sections.appendChild(sec);
    }
}


async function renderCategoryPage(category) {
    // show featured 8 items for this category and populate products grid with default per_page
    const all = await fetch('/api/products?per_page=1000').then(r => r.json());
    const items = all.products.filter(p => p.category === category);
    // show top 8 in featured
    renderFeatured(items.slice(0, 8));
    // load first page for product grid (uses currentCategory in fetchProducts)
    currentCategory = category;
    fetchProducts(1);

    // wire up view all button to show all items (no pagination)
    const viewAllBtn = document.getElementById('viewAllBtn');
    if (viewAllBtn) {
        viewAllBtn.onclick = (e) => {
            e.preventDefault();
            // render all items of this category
            renderProducts(items);
            const pag = document.getElementById('pagination'); if (pag) pag.innerHTML = '';
            const prod = document.getElementById('products'); if (prod) prod.scrollIntoView({ behavior: 'smooth' });
        };
    }
}


function renderFeatured(items) {
    const scroller = document.getElementById('featuredScroller');
    if (!scroller) return;
    scroller.innerHTML = '';
    for (const p of items) {
        const card = document.createElement('div');
        card.className = 'card product-card';
        card.innerHTML = `
            ${p.image_url ? `<div class="card-img-wrap"><img src="${p.image_url}" alt="${p.name}"></div>` : `<div class="card-img-wrap"><div class="placeholder-img"></div></div>`}
            <div class="card-body d-flex flex-column">
                <h6 class="card-title">${p.name}</h6>
                <div class="d-flex justify-content-between align-items-center mt-auto">
                  <span class="price-badge">${(typeof p.price_inr !== 'undefined' && p.price_inr !== null) ? '₹' + Number(p.price_inr).toFixed(2) : '$' + Number(p.price).toFixed(2)}</span>
                  <a class="btn btn-sm btn-primary" href="/product/${p.id}">View</a>
                </div>
            </div>
        `;
        scroller.appendChild(card);
    }
}
