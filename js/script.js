
const basePath = "/";

document.addEventListener("DOMContentLoaded", () => {


    const page = document.body.className;

    switch (page) {
        case "":
            index()
            break
        case "login":
            login()
            break

    }
    console.log(page)
});

function getURL(str) {
    return new URLSearchParams(window.location.search).get(str)
}

function index() {
    const imgInput = document.getElementById('img');
    const previewImg = document.querySelector('.pre_img');
    // const imgInput_sm = document.querySelector('.img_btn');
    const previewImg_sm = document.querySelector('.pre_img_sm');

    const chatBtn = document.getElementById('ai-chat-btn');
    const chatWindow = document.getElementById('ai-chat-window');
    const closeBtn = document.getElementById('chat-close-btn');
    const sendBtn = document.getElementById('chat-send-btn');
    const chatInput = document.getElementById('chat-input');


    // --- 事件監聽 ---
    const amountInput = document.getElementById('customAmount');

    // 2. 抓取所有金額按鈕 (用 Class)
    const buttons = document.querySelectorAll('.amount-btn');
    if (getURL('edit') == '7') {

        buttons.forEach(btn => {
            btn.addEventListener('click', function () {

                const value = this.getAttribute('data-amount');

                amountInput.value = value;

                buttons.forEach(b => b.classList.remove('selected'));

                this.classList.add('selected');
            });
        });


        amountInput.addEventListener('input', function () {
            buttons.forEach(btn => btn.classList.remove('selected'));
        });
    }

    const bankInput = document.getElementById('inputBank');
    const numInput = document.getElementById('inputNum');

    const displayBank = document.getElementById('displayBank');
    const displayNum = document.getElementById('displayNum');
    const cardLogo = document.getElementById('cardLogo');

    // 2. 定義完整的卡片規則 (Regex)
    const cardTypes = [
        { name: 'VISA', color: '#ffffff', pattern: /^4/ },
        { name: 'MasterCard', color: '#ff9f00', pattern: /^(5[1-5]|2[2-7])/ },
        { name: 'Amex', color: '#2e77bc', pattern: /^3[47]/ }, // 美國運通
        { name: 'JCB', color: '#006600', pattern: /^35/ },
        { name: 'UnionPay', color: '#00a1e9', pattern: /^62/ }, // 銀聯
        { name: 'Diners', color: '#888888', pattern: /^3(?:0[0-5]|[689])/ },
        { name: 'Discover', color: '#ff6600', pattern: /^6(?:011|5)/ },
        { name: 'Maestro', color: '#004c97', pattern: /^(5018|5020|5038|6304|6759|676[1-3])/ }
    ];

    function updateCardView() {
        // --- 更新銀行名稱 ---
        if (bankInput && displayBank) {
            displayBank.innerText = bankInput.value || 'BANK NAME';
        }

        // --- 更新卡號 (核心邏輯) ---
        if (numInput && displayNum) {

            let rawVal = numInput.value.replace(/\D/g, '');


            if (rawVal.length > 16) {
                rawVal = rawVal.substring(0, 16);
            }

            let formatted = rawVal.match(/.{1,4}/g)?.join(' ') || rawVal;


            if (numInput.value !== formatted) {
                numInput.value = formatted;
            }

            // E. 更新預覽圖的文字 (如果空了就顯示預設符號)
            displayNum.innerText = formatted || '#### #### #### ####';

            // F. 判斷卡別 Logo
            if (cardLogo) {
                let match = null;
                for (let card of cardTypes) {
                    if (card.pattern.test(rawVal)) {
                        match = card;
                        break;
                    }
                }

                if (match) {
                    cardLogo.innerText = match.name;
                    cardLogo.style.color = match.color;
                    cardLogo.style.opacity = '1';
                } else {
                    cardLogo.innerText = 'CARD';
                    cardLogo.style.color = '#fff';
                    cardLogo.style.opacity = '0.7';
                }
            }
        }
    }

    // 3. 綁定監聽事件
    if (bankInput) bankInput.addEventListener('input', updateCardView);
    if (numInput) numInput.addEventListener('input', updateCardView);


    chatBtn.addEventListener('click', function () {
        if (chatWindow.style.display === 'none' || chatWindow.style.display === '') {
            chatWindow.style.display = 'flex';

            setTimeout(() => chatInput.focus(), 100);
        } else {
            chatWindow.style.display = 'none';
        }
    });


    closeBtn.addEventListener('click', function () {
        chatWindow.style.display = 'none';
    });

    sendBtn.addEventListener('click', sendMessage);


    chatInput.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });


    // --- 傳送訊息的核心邏輯 ---
    async function sendMessage() {
        const input = document.getElementById('chat-input');
        const chatBody = document.getElementById('chat-body');
        const msg = input.value.trim();

        if (!msg) return;

        appendMessage(msg, 'user-message');
        input.value = '';

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'typing';
        loadingDiv.innerText = 'AI 正在思考中...';
        chatBody.appendChild(loadingDiv);
        chatBody.scrollTop = chatBody.scrollHeight;

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });

            const data = await response.json();

            chatBody.removeChild(loadingDiv);

            if (data.reply) {
                appendMessage(data.reply, 'ai-message');
            } else {
                appendMessage('系統發生錯誤，請稍後再試。', 'ai-message');
            }

        } catch (error) {
            if (chatBody.contains(loadingDiv)) {
                chatBody.removeChild(loadingDiv);
            }
            appendMessage('連線失敗，請檢查網路。', 'ai-message');
            console.error('Error:', error);
        }
    }

    function appendMessage(text, className) {
        const chatBody = document.getElementById('chat-body');
        const div = document.createElement('div');
        div.className = `message ${className}`;
        div.innerHTML = text.replace(/\n/g, '<br>');
        chatBody.appendChild(div);
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    let isDragging = false;
    let offsetX, offsetY;

    const chatHeader = document.querySelector('.chat-header');

    chatHeader.addEventListener('mousedown', function (e) {

        if (e.target === closeBtn) return;

        isDragging = true;

        const rect = chatWindow.getBoundingClientRect();
        offsetX = e.clientX - rect.left;
        offsetY = e.clientY - rect.top;

        chatWindow.style.opacity = '0.9';
    });

    document.addEventListener('mousemove', function (e) {
        if (!isDragging) return;

        e.preventDefault();

        const x = e.clientX - offsetX;
        const y = e.clientY - offsetY;

        chatWindow.style.left = `${x}px`;
        chatWindow.style.top = `${y}px`;


        chatWindow.style.bottom = 'auto';
        chatWindow.style.right = 'auto';
    });


    document.addEventListener('mouseup', function () {
        isDragging = false;
        chatWindow.style.opacity = '1';
    });

    function calculateTotal() {
        const inputs = document.querySelectorAll('input.count');
        let total = 0;

        inputs.forEach(input => {
            const qty = parseInt(input.value) || 0;
            const price = parseFloat(input.dataset.price) || 0;
            total += qty * price;
        });

        document.getElementById('total').textContent = total;
    }

    if (getURL('edit') == '1' || getURL('upd')) {
        calculateTotal()
    }

    document.querySelectorAll('input.count').forEach(input => {
        input.addEventListener('input', calculateTotal);
    });
    if (imgInput) {

        imgInput.addEventListener('change', function () {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewImg.src = e.target.result;

                }
                reader.readAsDataURL(file);
            } else {
                previewImg.src = "";

            }
            console.log(file);

        });
        document.querySelectorAll('.img_btn').forEach(input => {
            input.addEventListener('change', function () {

                console.log(this.id);

                const id = this.id.replace('img_sm_', '');
                const previewImg_sm = document.getElementById('pre_img_sm_' + id);

                const file = this.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = e => {
                    previewImg_sm.src = e.target.result;
                };
                reader.readAsDataURL(file);
            });
        });

    }
}
function login() {
    const refreshBtn = document.getElementById('refreshCaptcha');
    const captchaImg = document.getElementById('captcha_img');
    const clearBtn = document.getElementById('clear');
    const captchaUrl = captchaImg.dataset.url;
    let isLog = true;  // true = 登入, false = 註冊


    document.getElementById("goRegister").addEventListener("click", () => {
        isLog = false;
        updateUI();
    });

    document.getElementById("goLogin").addEventListener("click", () => {
        isLog = true;
        updateUI();
    });

    function updateUI() {
        if (isLog) {
            document.getElementById("loginHeader").classList.remove("d-none");
            document.getElementById("contentLogin").classList.remove("d-none");
            document.getElementById("registerHeader").classList.add("d-none");
            document.getElementById("contentRegister").classList.add("d-none");
        } else {
            document.getElementById("registerHeader").classList.remove("d-none");
            document.getElementById("contentRegister").classList.remove("d-none");
            document.getElementById("loginHeader").classList.add("d-none");
            document.getElementById("contentLogin").classList.add("d-none");
        }
    }

    clearBtn.addEventListener('click', function () {
        document.getElementById('acc').value = '';
        document.getElementById('ps').value = '';
        document.getElementById('captcha').value = '';
    })
    refreshBtn.addEventListener('click', function () {
        captchaImg.src = captchaUrl + "?t=" + new Date().getTime();
    });
}

