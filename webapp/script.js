const tg = window.Telegram.WebApp;

// --- ДАННЫЕ (в реальном проекте они будут приходить с бэкенда) ---
const products = [
    { id: 1, title: 'Жидкость "Лесные ягоды"', price: 500, description: "Сладкий микс лесных ягод" },
    { id: 2, title: 'Жидкость "Холодный манго"', price: 550, description: "Тропический манго с холодком" },
    { id: 3, title: 'Жидкость "Табак с вишней"', price: 480, description: "Классический вкус с ноткой вишни" }
];

const cart = [];

const productList = document.getElementById('product-list');
const cartItemsContainer = document.getElementById('cart-items');
const totalPriceEl = document.getElementById('total-price');
const checkoutBtn = document.getElementById('checkout-btn');

// --- ФУНКЦИИ ---

function renderProducts() {
    productList.innerHTML = '';
    products.forEach(product => {
        const productEl = document.createElement('div');
        productEl.className = 'product-item';
        productEl.innerHTML = `
            <h3>${product.title}</h3>
            <p>${product.description}</p>
            <p><strong>Цена: ${product.price} руб.</strong></p>
            <button onclick="addToCart(${product.id})">Добавить в корзину</button>
        `;
        productList.appendChild(productEl);
    });
}

function addToCart(productId) {
    const product = products.find(p => p.id === productId);
    const cartItem = cart.find(item => item.id === productId);

    if (cartItem) {
        cartItem.quantity++;
    } else {
        cart.push({ ...product, quantity: 1 });
    }
    renderCart();
}

function renderCart() {
    cartItemsContainer.innerHTML = '';
    if (cart.length === 0) {
        cartItemsContainer.innerHTML = '<p>Корзина пуста</p>';
        checkoutBtn.classList.add('hidden'); // Прячем кнопку, если корзина пуста
        return;
    }

    let totalPrice = 0;
    cart.forEach(item => {
        const itemEl = document.createElement('div');
        itemEl.className = 'cart-item';
        itemEl.innerText = `${item.title} x${item.quantity} - ${item.price * item.quantity} руб.`;
        cartItemsContainer.appendChild(itemEl);
        totalPrice += item.price * item.quantity;
    });

    totalPriceEl.innerText = totalPrice;
    checkoutBtn.classList.remove('hidden'); // Показываем кнопку
}

// --- ИНИЦИАЛИЗАЦИЯ И СОБЫТИЯ ---

// Вызывается, когда Web App готово к отображению
tg.ready();

// Настраиваем главную кнопку Telegram
tg.MainButton.setText('Перейти к оплате');
tg.MainButton.hide(); // Сначала прячем

// Обработчик нажатия на главную кнопку
tg.MainButton.onClick(() => {
    const orderData = {
        items: cart,
        total_price: cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
    };
    // Отправляем данные в бот
    tg.sendData(JSON.stringify(orderData));
});

// Логика кнопки "Оформить заказ" в HTML
checkoutBtn.addEventListener('click', () => {
    // Показываем главную кнопку Telegram, когда пользователь готов оформить заказ
    tg.MainButton.show();
});


// Первая отрисовка
renderProducts();
renderCart();
