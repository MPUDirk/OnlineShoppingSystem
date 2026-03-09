// 全局变量
let currentUser = null;
let cart = [];
let orders = [];
let products = [];
let currentProduct = null;
let currentCategoryProducts = null;
let currentCategoryName = '';

// 模拟商品数据
const mockProducts = [
    {
        id: 1,
        name: "智能手机",
        price: 2999,
        description: "最新款智能手机，配备高性能处理器和优质摄像头",
        image_url: "https://via.placeholder.com/250x200?text=智能手机",
        brand: "科技品牌",
        category: "电子产品",
        stock: 50,
        rating: "4.5"
    },
    {
        id: 2,
        name: "无线耳机",
        price: 299,
        description: "高品质无线蓝牙耳机，降噪效果出色",
        image_url: "https://via.placeholder.com/250x200?text=无线耳机",
        brand: "音频专家",
        category: "电子产品",
        stock: 30,
        rating: "4.3"
    },
    {
        id: 3,
        name: "运动鞋",
        price: 599,
        description: "舒适透气的运动鞋，适合日常运动和休闲穿着",
        image_url: "https://via.placeholder.com/250x200?text=运动鞋",
        brand: "运动品牌",
        category: "服装",
        stock: 25,
        rating: "4.2"
    },
    {
        id: 4,
        name: "编程书籍",
        price: 89,
        description: "Python编程从入门到精通，适合初学者",
        image_url: "https://via.placeholder.com/250x200?text=编程书籍",
        brand: "出版社",
        category: "图书",
        stock: 100,
        rating: "4.7"
    },
    {
        id: 5,
        name: "咖啡机",
        price: 1299,
        description: "全自动咖啡机，一键制作美味咖啡",
        image_url: "https://via.placeholder.com/250x200?text=咖啡机",
        brand: "家电品牌",
        category: "家居",
        stock: 15,
        rating: "4.4"
    },
    {
        id: 6,
        name: "背包",
        price: 199,
        description: "大容量双肩背包，适合旅行和日常使用",
        image_url: "https://via.placeholder.com/250x200?text=背包",
        brand: "户外品牌",
        category: "服装",
        stock: 40,
        rating: "4.1"
    },
    {
        id: 7,
        name: "4K显示器",
        price: 1599,
        description: "27英寸4K超高清显示器，色彩还原精准",
        image_url: "https://via.placeholder.com/250x200?text=4K显示器",
        brand: "显示专家",
        category: "电子产品",
        stock: 20,
        rating: "4.8"
    },
    {
        id: 8,
        name: "机械键盘",
        price: 499,
        description: "RGB背光机械键盘，青轴手感清脆",
        image_url: "https://via.placeholder.com/250x200?text=机械键盘",
        brand: "外设大厂",
        category: "电子产品",
        stock: 60,
        rating: "4.6"
    },
    {
        id: 9,
        name: "纯棉T恤",
        price: 59,
        description: "100%纯棉基础款T恤，舒适吸汗",
        image_url: "https://via.placeholder.com/250x200?text=纯棉T恤",
        brand: "休闲服饰",
        category: "服装",
        stock: 200,
        rating: "4.4"
    },
    {
        id: 10,
        name: "牛仔裤",
        price: 199,
        description: "经典直筒牛仔裤，耐磨耐穿",
        image_url: "https://via.placeholder.com/250x200?text=牛仔裤",
        brand: "时尚丹宁",
        category: "服装",
        stock: 150,
        rating: "4.3"
    },
    {
        id: 11,
        name: "科幻小说集",
        price: 128,
        description: "经典科幻小说合集，探索未来世界",
        image_url: "https://via.placeholder.com/250x200?text=科幻小说",
        brand: "科幻世界",
        category: "图书",
        stock: 80,
        rating: "4.9"
    },
    {
        id: 12,
        name: "烹饪大全",
        price: 68,
        description: "包含1000道家常菜谱，图文并茂",
        image_url: "https://via.placeholder.com/250x200?text=烹饪大全",
        brand: "美食生活",
        category: "图书",
        stock: 120,
        rating: "4.7"
    },
    {
        id: 13,
        name: "空气净化器",
        price: 899,
        description: "家用静音空气净化器，去除甲醛和PM2.5",
        image_url: "https://via.placeholder.com/250x200?text=空气净化器",
        brand: "健康家电",
        category: "家居",
        stock: 35,
        rating: "4.6"
    },
    {
        id: 14,
        name: "乳胶枕头",
        price: 158,
        description: "天然乳胶枕头，护颈助眠",
        image_url: "https://via.placeholder.com/250x200?text=乳胶枕头",
        brand: "睡眠专家",
        category: "家居",
        stock: 100,
        rating: "4.5"
    },
    {
        id: 15,
        name: "平板电脑",
        price: 3299,
        description: "轻薄便携平板电脑，办公娱乐两不误",
        image_url: "https://via.placeholder.com/250x200?text=平板电脑",
        brand: "科技品牌",
        category: "电子产品",
        stock: 45,
        rating: "4.7"
    },
    {
        id: 16,
        name: "运动外套",
        price: 399,
        description: "防风防水运动外套，户外运动必备",
        image_url: "https://via.placeholder.com/250x200?text=运动外套",
        brand: "运动品牌",
        category: "服装",
        stock: 60,
        rating: "4.4"
    },
    {
        id: 17,
        name: "历史传记",
        price: 55,
        description: "名人历史传记，了解伟大人物的一生",
        image_url: "https://via.placeholder.com/250x200?text=历史传记",
        brand: "历史书局",
        category: "图书",
        stock: 90,
        rating: "4.6"
    },
    {
        id: 18,
        name: "扫地机器人",
        price: 1999,
        description: "智能规划路线，自动回充扫地机器人",
        image_url: "https://via.placeholder.com/250x200?text=扫地机器人",
        brand: "智能家居",
        category: "家居",
        stock: 25,
        rating: "4.8"
    }
];

// 初始化
document.addEventListener('DOMContentLoaded', function () {
    // 尝试从 localStorage 加载商品，如果不存在则使用模拟数据
    const savedProducts = localStorage.getItem('products');
    if (savedProducts) {
        products = JSON.parse(savedProducts);
    } else {
        products = [...mockProducts];
        localStorage.setItem('products', JSON.stringify(products));
    }

    renderFeaturedProducts();
    renderNewArrivals();
    renderProducts();
    updateCategoryCounts();
    updateCartDisplay();
    loadOrders();
});

// 更新分类商品数量
function updateCategoryCounts() {
    const categories = {
        'electronics': '电子产品',
        'clothing': '服装',
        'books': '图书',
        'home': '家居'
    };

    for (const [key, value] of Object.entries(categories)) {
        const count = products.filter(p => (p.category || '').trim() === value).length;
        const element = document.getElementById(`count-${key}`);
        if (element) {
            element.textContent = `${count} 件商品`;
        }
    }
}

// 页面切换
function showPage(pageId) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));
    document.getElementById(pageId).classList.add('active');

    if (pageId === 'products') {
        renderProducts('', currentCategoryProducts, currentCategoryName);
    } else if (pageId === 'cart') {
        renderCart();
    } else if (pageId === 'orders') {
        renderOrders();
    }
}

function showAllProducts() {
    currentCategoryProducts = null;
    currentCategoryName = '';
    showPage('products');
}

// 用户注册
/*function register(event) {
    event.preventDefault();
    const fullName = document.getElementById('regFullName').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;
    const address = document.getElementById('regAddress').value;

    if (password !== confirmPassword) {
        showMessage('registerMessage', '密码不匹配', 'error');
        return;
    }

    // 注册成功
    currentUser = {username: email, fullName, email, address};
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    updateNavigation();
    showPage('home');
    showMessage('registerMessage', '注册成功！', 'success');
}*/

// 用户登录
/*function login(event) {
    event.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    // 登录成功
    currentUser = {username, fullName: '测试用户', email: username, address: '测试地址'};
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    updateNavigation();
    showPage('home');
    showMessage('loginMessage', '登录成功！', 'success');
}*/

// 退出登录
/*function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    updateNavigation();
    showPage('home');
}*/

// 更新导航栏
function updateNavigation() {
    const userInfo = document.getElementById('userInfo');
    const cartLink = document.getElementById('cartLink');
    const ordersLink = document.getElementById('ordersLink');
    const logoutLink = document.getElementById('logoutLink');
    const loginLinks = document.getElementById('loginLinks');

    if (currentUser) {
        userInfo.textContent = `欢迎, ${currentUser.username}`;
        userInfo.classList.remove('hidden');
        cartLink.classList.remove('hidden');
        ordersLink.classList.remove('hidden');
        logoutLink.classList.remove('hidden');
        loginLinks.classList.add('hidden');
    } else {
        userInfo.classList.add('hidden');
        cartLink.classList.add('hidden');
        ordersLink.classList.add('hidden');
        logoutLink.classList.add('hidden');
        loginLinks.classList.remove('hidden');
    }
}

// 显示消息
function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    setTimeout(() => {
        element.innerHTML = '';
    }, 3000);
}

// 渲染热门商品
function renderFeaturedProducts() {
    const container = document.getElementById('featuredProducts');
    // 只显示前3个商品，确保在有侧边栏的情况下只显示一行
    const featured = products.slice(0, 3);
    container.innerHTML = featured.map(product => `
                <div class="product-card">
                    <img src="${product.image_url}" alt="${product.name}" class="product-image">
                    <div class="product-info">
                        <h3 class="product-title">${product.name}</h3>
                        <p class="product-price">¥${product.price}</p>
                        <p style="color: #666; font-size: 0.9rem; margin: 0.5rem 0;">${product.description.substring(0, 50)}...</p>
                        <div class="product-actions">
                            <button class="btn btn-primary" style="width: 100%;" onclick="showProductDetail(${product.id})">查看详情</button>
                        </div>
                    </div>
                </div>
            `).join('');
}

// 渲染新品上市
function renderNewArrivals() {
    const container = document.getElementById('newArrivals');
    // 获取最新的3个商品（这里简单地取后3个作为示例，实际应根据ID或日期排序）
    const newProducts = products.slice(-3).reverse();
    container.innerHTML = newProducts.map(product => `
                <div class="product-card">
                    <img src="${product.image_url}" alt="${product.name}" class="product-image">
                    <div class="product-info">
                        <h3 class="product-title">${product.name}</h3>
                        <p class="product-price">¥${product.price}</p>
                        <p style="color: #666; font-size: 0.9rem; margin: 0.5rem 0;">${product.description.substring(0, 50)}...</p>
                        <div class="product-actions">
                            <button class="btn btn-primary" style="width: 100%;" onclick="showProductDetail(${product.id})">查看详情</button>
                        </div>
                    </div>
                </div>
            `).join('');
}

// 渲染商品列表
function renderProducts(searchTerm = '', categoryProducts = null, categoryName = '') {
    const container = document.getElementById('productGrid');
    let filteredProducts = categoryProducts !== null ? categoryProducts : products;

    if (searchTerm) {
        filteredProducts = filteredProducts.filter(product =>
            product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            product.description.toLowerCase().includes(searchTerm.toLowerCase())
        );
    }

    // 更新标题和商品数量
    const titleElement = document.getElementById('categoryTitle');
    if (categoryName) {
        titleElement.textContent = categoryName;
    } else if (searchTerm) {
        titleElement.textContent = `搜索结果: "${searchTerm}"`;
    } else {
        titleElement.textContent = '商品列表';
    }

    document.getElementById('productCount').textContent = `共 ${filteredProducts.length} 件商品`;

    container.innerHTML = filteredProducts.map(product => `
                <div class="product-card">
                    <img src="${product.image_url}" alt="${product.name}" class="product-image">
                    <div class="product-info">
                        <h3 class="product-title">${product.name}</h3>
                        <p class="product-price">¥${product.price}</p>
                        <p style="color: #666; font-size: 0.9rem; margin: 0.5rem 0;">${product.description.substring(0, 50)}...</p>
                        <div class="product-actions">
                            <button class="btn btn-primary" style="width: 100%;" onclick="showProductDetail(${product.id})">查看详情</button>
                        </div>
                    </div>
                </div>
            `).join('');
}

// 搜索商品
function searchProducts(event) {
    event.preventDefault();
    const searchTerm = event.target.querySelector('input').value;
    renderProducts(searchTerm, currentCategoryProducts, currentCategoryName);

    const productsPage = document.getElementById('products');
    if (!productsPage.classList.contains('active')) {
        showPage('products');
    }
}

// 按分类筛选
function filterByCategory(category) {
    const categoryNames = {
        'electronics': '电子产品',
        'clothing': '服装',
        'books': '图书',
        'home': '家居'
    };
    const categoryName = categoryNames[category] || category;
    const filtered = products.filter(product => (product.category || '').trim() === categoryName);

    currentCategoryName = categoryName;
    currentCategoryProducts = filtered;
    showPage('products');
}

// 显示商品详情
function showProductDetail(productId) {
    currentProduct = products.find(p => p.id === productId);
    const container = document.getElementById('productDetailContent');

    container.innerHTML = `
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    <div>
                        <img src="${currentProduct.image_url}" alt="${currentProduct.name}" style="width: 100%; max-width: 400px; height: auto; border-radius: 8px;">
                    </div>
                    <div>
                        <h1>${currentProduct.name}</h1>
                        <p class="product-price" style="font-size: 1.5rem; margin: 1rem 0;">¥${currentProduct.price}</p>
                        
                        <div style="margin: 1.5rem 0;">
                            <h3>商品描述</h3>
                            <p style="color: #666; line-height: 1.6;">${currentProduct.description}</p>
                        </div>
                        
                        <div style="margin: 1.5rem 0;">
                            <h3>商品属性</h3>
                            <div style="background: #f8f9fa; padding: 1rem; border-radius: 4px;">
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                    <div><strong>品牌:</strong> ${currentProduct.brand}</div>
                                    <div><strong>分类:</strong> ${currentProduct.category}</div>
                                    <div><strong>库存:</strong> ${currentProduct.stock} 件</div>
                                    <div><strong>评分:</strong> ${currentProduct.rating}</div>
                                </div>
                            </div>
                        </div>
                        
                        ${currentUser ? `
                            <div style="margin-top: 2rem;">
                                <div class="form-group">
                                    <label for="quantity" class="form-label">数量</label>
                                    <input type="number" class="form-control" id="quantity" value="1" min="1" max="${currentProduct.stock}" style="width: 100px;">
                                </div>
                                ${currentProduct.stock > 0 ?
        `<button class="btn btn-success" style="width: 100%;" onclick="addToCart(${currentProduct.id})">加入购物车</button>` :
        `<button class="btn" disabled style="width: 100%; background-color: #ccc;">商品缺货</button>`
    }
                            </div>
                        ` : `
                            <div style="margin-top: 2rem; padding: 1rem; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px;">
                                <p style="margin: 0;">请先 <a href="/user/login/">登录</a> 后再购买商品</p>
                            </div>
                        `}
                    </div>
                </div>
                
                <div class="card" style="margin-top: 2rem;">
                    <h3>相关产品推荐</h3>
                    <div class="product-grid" style="margin-top: 1rem;">
                        ${products.filter(p => (p.category || '').trim() === (currentProduct.category || '').trim() && p.id !== currentProduct.id)
        .slice(0, 3).map(product => `
                            <div class="product-card">
                                <img src="${product.image_url}" alt="${product.name}" class="product-image">
                                <div class="product-info">
                                    <h4 class="product-title">${product.name}</h4>
                                    <p class="product-price">¥${product.price}</p>
                                    <div class="product-actions">
                                        <button class="btn btn-primary" style="width: 100%;" onclick="showProductDetail(${product.id})">查看详情</button>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;

    showPage('productDetail');
}

// 添加到购物车
function addToCart(productId) {
    if (!currentUser) {
        window.location.href = '/user/login/';
        return;
    }

    const quantity = parseInt(document.getElementById('quantity').value);
    const product = products.find(p => p.id === productId);

    const existingItem = cart.find(item => item.product.id === productId);
    const currentQuantity = existingItem ? existingItem.quantity : 0;

    if (product.stock < quantity + currentQuantity) {
        alert('库存不足，当前购物车已有 ' + currentQuantity + ' 件，库存剩余 ' + product.stock + ' 件');
        return;
    }

    if (existingItem) {
        existingItem.quantity += quantity;
    } else {
        cart.push({
            id: Date.now(),
            product: product,
            quantity: quantity
        });
    }

    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartDisplay();
    alert('商品已添加到购物车！');
    showPage('cart');
}

// 更新购物车显示
function updateCartDisplay() {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
        cart = JSON.parse(savedCart);
    }
}

// 渲染购物车
function renderCart() {
    const container = document.getElementById('cartContent');

    if (cart.length === 0) {
        container.innerHTML = `
                    <div class="text-center" style="padding: 3rem;">
                        <p style="color: #666; font-size: 1.1rem; margin-bottom: 1rem;">购物车是空的</p>
                        <button class="btn btn-primary" onclick="showAllProducts()">去购物</button>
                    </div>
                `;
        return;
    }

    const totalPrice = cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);

    container.innerHTML = `
                <form onsubmit="updateCart(event)">
                    ${cart.map(item => `
                        <div class="cart-item">
                            <div class="cart-item-info">
                                <h4><a href="#" onclick="showProductDetail(${item.product.id})" style="text-decoration: none; color: #2c3e50;">${item.product.name}</a></h4>
                                <p style="color: #666; font-size: 0.9rem;">${item.product.description.substring(0, 50)}...</p>
                                
                                <div style="margin-top: 0.5rem;">
                                    <label style="margin-right: 0.5rem;">数量:</label>
                                    <input type="number" value="${item.quantity}" min="1" max="${item.product.stock}" 
                                           onchange="updateCartItemQuantity(${item.id}, this.value)" 
                                           style="width: 60px; padding: 0.25rem; border: 1px solid #ddd; border-radius: 4px;">
                                    
                                    <button type="button" class="btn btn-danger" style="margin-left: 1rem; padding: 0.25rem 0.5rem; font-size: 0.9rem;" onclick="removeFromCart(${item.id})">删除</button>
                                </div>
                                
                                ${item.product.stock < item.quantity ?
        `<p style="color: #e74c3c; font-size: 0.8rem; margin-top: 0.5rem;">库存不足，仅剩 ${item.product.stock} 件</p>` : ''
    }
                            </div>
                            
                            <div class="cart-item-price">
                                ¥${item.product.price}
                            </div>
                        </div>
                    `).join('')}
                    
                    <div class="cart-total">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <button type="submit" class="btn btn-primary">更新购物车</button>
                            </div>
                            <div>
                                <strong>总计: ¥${totalPrice}</strong>
                            </div>
                        </div>
                    </div>
                </form>
                
                <div style="text-align: right; margin-top: 1rem;">
                    <button class="btn btn-success" style="padding: 1rem 2rem; font-size: 1.1rem;" onclick="checkout()">去结算</button>
                </div>
            `;
}

// 更新购物车商品数量
function updateCartItemQuantity(itemId, newQuantity) {
    const item = cart.find(item => item.id === itemId);
    if (item) {
        let qty = parseInt(newQuantity);
        if (isNaN(qty) || qty < 1) {
            qty = 1;
        }

        if (qty > item.product.stock) {
            alert('库存不足，最大库存为 ' + item.product.stock);
            qty = item.product.stock;
        }

        item.quantity = qty;
        localStorage.setItem('cart', JSON.stringify(cart));
        renderCart();
    }
}

// 从购物车删除商品
function removeFromCart(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    localStorage.setItem('cart', JSON.stringify(cart));
    renderCart();
}

// 更新购物车
function updateCart(event) {
    event.preventDefault();
    renderCart();
}

// 结算
function checkout() {
    if (cart.length === 0) {
        alert('购物车是空的');
        return;
    }

    const orderNumber = 'ORD' + Date.now();
    const totalAmount = cart.reduce((sum, item) => sum + (item.product.price * item.quantity), 0);

    const order = {
        id: Date.now(),
        order_number: orderNumber,
        total_amount: totalAmount,
        status: 'pending',
        created_at: new Date().toISOString(),
        items: cart.map(item => ({
            product: item.product,
            quantity: item.quantity,
            unit_price: item.product.price,
            subtotal: item.product.price * item.quantity
        }))
    };

    orders.unshift(order);
    localStorage.setItem('orders', JSON.stringify(orders));

    // 清空购物车
    cart = [];
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartDisplay();

    showPage('orders');
    setTimeout(() => {
        alert('订单已创建！订单号：' + orderNumber);
    }, 100);
}

// 加载订单
function loadOrders() {
    const savedOrders = localStorage.getItem('orders');
    if (savedOrders) {
        orders = JSON.parse(savedOrders);
    }
}

// 渲染订单列表
function renderOrders(statusFilter = '') {
    const container = document.getElementById('ordersList');
    let filteredOrders = orders;

    if (statusFilter) {
        filteredOrders = orders.filter(order => order.status === statusFilter);
    }

    if (filteredOrders.length === 0) {
        container.innerHTML = `
                    <div class="text-center" style="padding: 3rem;">
                        <p style="color: #666; font-size: 1.1rem;">暂无订单</p>
                    </div>
                `;
        return;
    }

    container.innerHTML = filteredOrders.map(order => `
                <div class="order-item">
                    <div class="order-header">
                        <div>
                            <strong>订单号: ${order.order_number}</strong>
                            <br>
                            <small style="color: #666;">下单时间: ${new Date(order.created_at).toLocaleString()}</small>
                        </div>
                        <div style="text-align: right;">
                            <span class="order-status status-${order.status}">
                                ${getStatusText(order.status)}
                            </span>
                            <br>
                            <strong style="color: #e74c3c;">¥${order.total_amount}</strong>
                        </div>
                    </div>
                    
                    <div style="padding: 1rem;">
                        <h4>商品清单</h4>
                        <div style="background: #f8f9fa; padding: 1rem; border-radius: 4px; margin-top: 0.5rem;">
                            ${order.items.map(item => `
                                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #eee;">
                                    <div>
                                        <strong>${item.product ? item.product.name : '未知商品'}</strong>
                                        <br>
                                        <small style="color: #666;">数量: ${item.quantity}</small>
                                    </div>
                                    <div style="text-align: right;">
                                        <div>¥${item.unit_price}</div>
                                        <div style="color: #e74c3c; font-weight: bold;">¥${item.subtotal}</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        
                        <div style="text-align: right; margin-top: 1rem;">
                            ${order.status === 'pending' ?
        `<button class="btn btn-danger" onclick="cancelOrder(${order.id})">取消订单</button>` : ''
    }
                        </div>
                    </div>
                </div>
            `).join('');
}

// 获取状态文本
function getStatusText(status) {
    const statusMap = {
        'pending': '待处理',
        'shipped': '已发货',
        'delivered': '已送达',
        'cancelled': '已取消'
    };
    return statusMap[status] || status;
}

// 筛选订单
function filterOrders() {
    const statusFilter = document.getElementById('orderStatusFilter').value;
    renderOrders(statusFilter);
}

// 取消订单
function cancelOrder(orderId) {
    if (confirm('确定要取消此订单吗？')) {
        const order = orders.find(o => o.id === orderId);
        if (order) {
            order.status = 'cancelled';
            order.status_changed_at = new Date().toISOString();
            localStorage.setItem('orders', JSON.stringify(orders));
            renderOrders();
        }
    }
}

// 检查登录状态
function checkLoginStatus() {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateNavigation();
    }
}

// 页面加载时检查登录状态
checkLoginStatus();
