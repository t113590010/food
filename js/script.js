
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
    const imgInput_sm = document.getElementById('img_sm');
    const previewImg_sm = document.querySelector('.pre_img_sm');
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

    if (getURL('edit') == '1' || getURL('upd') == '5') {
        calculateTotal()
    }

    document.querySelectorAll('input.count').forEach(input => {
        input.addEventListener('input', calculateTotal);
    });
    if (imgInput && imgInput_sm) {

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
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', function () {
                const file = this.files[0];
                const previewId = `pre_img_sm_${this.id}`;  
                const previewImg = document.getElementById(previewId);

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

