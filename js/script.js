
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

