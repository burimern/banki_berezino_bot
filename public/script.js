document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram.WebApp;
    tg.ready();

    const productListEl = document.getElementById('product-list');
    const cartItemsEl = document.getElementById('cart-items');
    const totalPriceEl = document.getElementById('total-price');
    const cartSectionEl = document.getElementById('cart-section');
    const errorEl = document.getElementById('error-message');

    let products = [];
    let cart = {}; // {productId: quantity}

    // --- ФУНКЦИИ ---

    async function fetchProducts() {
        try {
            // Запрос к нашему API на Vercel
            const response = await fetch('/api/products');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            products = await response.json();
            renderProducts();
        } catch (error) {
            console.error("Failed to fetch products:", error);
            showError("Не удалось загрузить товары. Попробуйте позже.");
            productListEl.innerHTML = '';
        }
    }

    function renderProducts() {
        productListEl.innerHTML = '';
        if (products.length === 0) {
            productListEl.innerHTML = '<p>Товаров пока нет.</p>';
            return;
        }

        products.forEach(product => {
            const productEl = document.createElement('div');
            productEl.className = 'product-item';
            productEl.innerHTML = `
                <h3>${product.title}</h3>
                <p class="price">Цена: ${product.price} руб.</p>
                <button class="add-to-cart-btn" data-product-id="${product.id}">Добавить в корзину</button>
            `;
            productListEl.appendChild(productEl);
        });
    }

    function addToCart(productId) {
        if (cart[productId]) {
            cart[productId]++;
        } else {
            cart[productId] = 1;
        }
        renderCart();
    }

    function renderCart() {
        cartItemsEl.innerHTML = '';
        let totalPrice = 0;
        let hasItems = false;

        for (const productId in cart) {
            if (cart[productId] > 0) {
                hasItems = true;
                const product = products.find(p => p.id == productId);
                if (product) {
                    const itemEl = document.createElement('div');
                    itemEl.className = 'cart-item';
                    itemEl.textContent = `${product.title} x${cart[productId]} — ${product.price * cart[productId]} руб.`;
                    cartItemsEl.appendChild(itemEl);
                    totalPrice += product.price * cart[productId];
                }
            }
        }
        
        totalPriceEl.textContent = totalPrice;

        if (hasItems) {
            cartSectionEl.classList.remove('hidden');
            tg.MainButton.setText(`Оформить заказ на ${totalPrice} руб.`);
            tg.MainButton.show();
        } else {
            cartSectionEl.classList.add('hidden');
            tg.MainButton.hide();
        }
    }

    function showError(message) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }

    // --- ОБРАБОТЧИКИ СОБЫТИЙ ---

    productListEl.addEventListener('click', (event) => {
        if (event.target.classList.contains('add-to-cart-btn')) {
            const productId = event.target.dataset.productId;
            addToCart(productId);
        }
    });

    tg.MainButton.onClick(() => {
        const orderData = {
            items: [],
            total_price: 0
        };
        let totalPrice = 0;

        for (const productId in cart) {
            const quantity = cart[productId];
            if (quantity > 0) {
                const product = products.find(p => p.id == productId);
                if (product) {
                    orderData.items.push({
                        id: product.id,
                        title: product.title,
                        price: product.price,
                        quantity: quantity
                    });
                    totalPrice += product.price * quantity;
                }
            }
        }
        orderData.total_price = totalPrice;
        
        // Отправляем данные в JSON-формате в бот
        tg.sendData(JSON.stringify(orderData));
    });

    // --- ИНИЦИАЛИЗАЦИЯ ---
    
    // Настраиваем кнопку "Назад", если она понадобится
    tg.BackButton.hide();
    
    // Запускаем загрузку товаров
    fetchProducts();
});
