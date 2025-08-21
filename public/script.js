document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    const catalogTitleEl = document.getElementById('catalog-title');
    const itemListEl = document.getElementById('item-list');
    const errorEl = document.getElementById('error-message');

    let catalogData = {};
    let cart = {}; // { productId: quantity }

    // --- Рендер брендов ---
    function renderBrands() {
        itemListEl.innerHTML = '';
        if (catalogTitleEl) catalogTitleEl.textContent = 'Каталог товаров';

        const brands = Object.keys(catalogData).sort();
        if (brands.length === 0) {
            itemListEl.innerHTML = '<p>Товаров пока нет.</p>';
            return;
        }

        brands.forEach(brandName => {
            const brandEl = document.createElement('div');
            brandEl.className = 'brand-card';
            brandEl.textContent = brandName;
            brandEl.onclick = () => renderProductsOfBrand(brandName);
            itemListEl.appendChild(brandEl);
        });
        tg.BackButton.hide();
    }

    // --- Рендер товаров бренда ---
    function renderProductsOfBrand(brandName) {
        itemListEl.innerHTML = '';
        if (catalogTitleEl) catalogTitleEl.textContent = brandName;

        const products = catalogData[brandName];
        products.sort((a, b) => a.name.localeCompare(b.name)).forEach(product => {
            const productEl = document.createElement('div');
            productEl.className = 'product-item';
            productEl.innerHTML = `
                <h3>${product.name}</h3>
                <p class="price">Цена: ${product.price} руб.</p>
                <div class="product-actions">
                    <button class="decrease-btn" data-product-id="${product.id}">−</button>
                    <span class="quantity" id="qty-${product.id}">${cart[product.id] || 0}</span>
                    <button class="increase-btn" data-product-id="${product.id}">+</button>
                </div>
            `;
            itemListEl.appendChild(productEl);
        });
        tg.BackButton.show();
    }

    // --- Добавить / уменьшить товар в корзине ---
    function changeCartQuantity(productId, delta) {
        cart[productId] = Math.max((cart[productId] || 0) + delta, 0);
        const qtyEl = document.getElementById(`qty-${productId}`);
        if (qtyEl) qtyEl.textContent = cart[productId];
        updateMainButton();
    }

    // --- Обновление главной кнопки ---
    function updateMainButton() {
        let totalPrice = 0;
        let totalItems = 0;

        for (const productId in cart) {
            const quantity = cart[productId];
            if (quantity > 0) {
                totalItems += quantity;
                for (const brand in catalogData) {
                    const product = catalogData[brand].find(p => p.id == productId);
                    if (product) {
                        totalPrice += product.price * quantity;
                        break;
                    }
                }
            }
        }

        if (totalItems > 0) {
            tg.MainButton.setText(`Отправить заказ на ${totalPrice} руб.`);
            tg.MainButton.show();
        } else {
            tg.MainButton.hide();
        }
    }

    function showError(message) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }

    // --- Загрузка каталога ---
    async function fetchCatalogData() {
        try {
            const response = await fetch('/api/products');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            catalogData = await response.json();
            renderBrands();
        } catch (error) {
            console.error("Failed to fetch catalog data:", error);
            showError("Не удалось загрузить товары. Попробуйте позже.");
        }
    }

    // --- События кнопок ---
    itemListEl.addEventListener('click', (event) => {
        const productId = event.target.dataset.productId;
        if (!productId) return;

        if (event.target.classList.contains('increase-btn')) {
            changeCartQuantity(productId, 1);
        } else if (event.target.classList.contains('decrease-btn')) {
            changeCartQuantity(productId, -1);
        }
    });

    tg.BackButton.onClick(() => {
        renderBrands();
    });

    tg.MainButton.onClick(() => {
        const orderData = { items: [], total_price: 0 };
        let totalPrice = 0;

        for (const productId in cart) {
            const quantity = cart[productId];
            if (quantity > 0) {
                for (const brand in catalogData) {
                    const product = catalogData[brand].find(p => p.id == productId);
                    if (product) {
                        orderData.items.push({
                            id: product.id,
                            name: product.name,
                            price: product.price,
                            quantity: quantity
                        });
                        totalPrice += product.price * quantity;
                        break;
                    }
                }
            }
        }
        orderData.total_price = totalPrice;
        tg.sendData(JSON.stringify(orderData));
    });

    fetchCatalogData();
});
