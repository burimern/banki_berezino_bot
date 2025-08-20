document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();

    const catalogTitleEl = document.getElementById('catalog-title'); // Предполагается, что у вас есть <h1> с этим ID
    const itemListEl = document.getElementById('item-list'); // Основной контейнер для брендов или товаров
    const errorEl = document.getElementById('error-message');

    let catalogData = {}; // Здесь будет храниться вся структура { "Brand": [products] }
    let cart = {}; // {productId: quantity}

    // --- ФУНКЦИИ ОТОБРАЖЕНИЯ ---

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
            brandEl.className = 'brand-card'; // Стилизуйте этот класс для красивого вида "папки"
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
            productEl.className = 'product-item'; // Ваш класс для карточки товара
            // ВАЖНО: В Python мы назвали поля 'name' и 'price', а не 'title'
            productEl.innerHTML = `
                <h3>${product.name}</h3>
                <p class="price">Цена: ${product.price} руб.</p>
                <button class="add-to-cart-btn" data-product-id="${product.id}" data-brand-name="${brandName}">Добавить в корзину</button>
            `;
            itemListEl.appendChild(productEl);
        });

        tg.BackButton.show();
    }

    // --- ФУНКЦИИ КОРЗИНЫ (Оставляем почти без изменений) ---

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
                // Ищем товар во всех брендах
                for (const brand in catalogData) {
                    const product = catalogData[brand].find(p => p.id == productId);
                    if (product) {
                        totalPrice += product.price * quantity;
                        totalItems += quantity;
                        break; // Выходим из внутреннего цикла, как только нашли товар
                    }
                }
            }
        }
        
        if (totalItems > 0) {
            tg.MainButton.setText(`Оформить заказ на ${totalPrice} руб.`);
            tg.MainButton.show();
        } else {
            tg.MainButton.hide();
        }
    }

    function showError(message) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }

    // --- ЗАГРУЗКА ДАННЫХ ---

    async function fetchCatalogData() {
        try {
            const response = await fetch('/api/products');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            catalogData = await response.json();
            renderBrands(); // Начинаем с отрисовки брендов
        } catch (error) {
            console.error("Failed to fetch catalog data:", error);
            showError("Не удалось загрузить товары. Попробуйте позже.");
        }
    }

    // --- ОБРАБОТЧИКИ СОБЫТИЙ ---

    itemListEl.addEventListener('click', (event) => {
        if (event.target.classList.contains('add-to-cart-btn')) {
            const productId = event.target.dataset.productId;
            addToCart(productId);
        }
    });
    
    // Кнопка "Назад" в Web App
    tg.BackButton.onClick(() => {
        renderBrands();
    });

    // Главная кнопка для оформления заказа
    tg.MainButton.onClick(() => {
        // Логика отправки данных в бот (немного адаптирована)
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

    // --- ИНИЦИАЛИЗАЦИЯ ---
    fetchCatalogData();
});
