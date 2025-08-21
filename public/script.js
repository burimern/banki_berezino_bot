document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    const catalogTitleEl = document.getElementById('catalog-title');
    const itemListEl = document.getElementById('item-list');
    const errorEl = document.getElementById('error-message');
    const cartBar = document.getElementById('cart-bar');
    const cartItemsEl = document.getElementById('cart-items-count');
    const cartTotalEl = document.getElementById('cart-total-price');

    let catalogData = {}; 
    let cart = {};

    function renderBrands() {
        itemListEl.innerHTML = '';
        if (catalogTitleEl) catalogTitleEl.textContent = 'Каталог товаров';
        
        const brands = Object.keys(catalogData);
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

    function renderProductsOfBrand(brandName) {
        itemListEl.innerHTML = '';
        if (catalogTitleEl) catalogTitleEl.textContent = brandName;

        const products = catalogData[brandName];
        products.forEach(product => {
            const productEl = document.createElement('div');
            productEl.className = 'product-item';
            productEl.innerHTML = `
                <h3>${product.name}</h3>
                <p class="price">Цена: ${product.price} руб.</p>
                <button class="add-to-cart-btn" data-product-id="${product.id}">Добавить в корзину</button>
            `;
            itemListEl.appendChild(productEl);
        });
        tg.BackButton.show();
    }

    function addToCart(productId) {
        cart[productId] = (cart[productId] || 0) + 1;
        updateMainButton();
    }
    
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

            cartItemsEl.textContent = totalItems;
            cartTotalEl.textContent = `${totalPrice} руб.`;
            cartBar.classList.remove('hidden');
        } else {
            tg.MainButton.hide();
            cartBar.classList.add('hidden');
        }
    }

    function showError(message) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }

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

    itemListEl.addEventListener('click', (event) => {
        if (event.target.classList.contains('add-to-cart-btn')) {
            const productId = event.target.dataset.productId;
            addToCart(productId);
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
                        orderData.items.push({ id: product.id, name: product.name, price: product.price, quantity: quantity });
                        totalPrice += product.price * quantity;
                        break;
                    }
                }
            }
        }
        orderData.total_price = totalPrice;
        tg.sendData(JSON.stringify(orderData));
    });

    // Клик по панели корзины имитирует MainButton
    cartBar.addEventListener('click', () => {
        tg.MainButton.click();
    });

    fetchCatalogData();
});
