document.addEventListener('DOMContentLoaded', function () {
    $(function () {
        // Nav active toggle
        $(".nav-link").click(function () {
            $(".nav-link").removeClass("active");
            $(this).addClass("active");
        });
    });

    // Modals for Login/Register/Yateem
    const modallY = document.getElementById("myModalyateem");
    const btnnn = document.getElementById("openModalyateem");
    const spannn = document.querySelector(".closeee");
    if (btnnn && spannn && modallY) {
        btnnn.onclick = function () { modallY.style.display = "block"; }
        spannn.onclick = function () { modallY.style.display = "none"; }
        window.onclick = function (event) {
            if (event.target == modallY) modallY.style.display = "none";
        }
    }


    // Login Modal
    const modal = document.getElementById("myModal");
    const btn = document.getElementById("openModalBtn");
    const span = document.querySelector(".close");
    if (btn && span && modal) {
        btn.onclick = function () { modal.style.display = "block"; }
        span.onclick = function () { modal.style.display = "none"; }
        window.onclick = function (event) {
            if (event.target == modal) modal.style.display = "none";
        }
    }

    // Register Modal open from Login
    const modd = document.getElementById("myModalRegister");
    const bbttn = document.getElementById("signupLink");
    const ssppan = document.querySelector(".close");
    if (bbttn && ssppan && modd) {
        bbttn.onclick = function () {
            modd.style.display = "block";
            if (modal) modal.style.display = "none";
        }
        ssppan.onclick = function () { modd.style.display = "none"; }
    }


    /* Login Modal open from Register */
    const bbtn = document.getElementById("loginLink");
    const sspan = document.querySelector(".close");
    if (bbtn && sspan && modal && modd) {
        bbtn.onclick = function () {
            modal.style.display = "block";
            modd.style.display = "none";
        }
        sspan.onclick = function () { modal.style.display = "none"; }
    }

    /* Direct Register open */
    const btnn = document.getElementById("openModalBtnRegister");
    const spann = document.querySelector(".closee");
    if (btnn && spann && modd) {
        btnn.onclick = function () { modd.style.display = "block"; }
        spann.onclick = function () { modd.style.display = "none"; }
    }

    /* File upload preview */
    function initFileUpload() {
        const fileInputs = document.querySelectorAll('#file-input');
        fileInputs.forEach(fileInput => {
            const preview = fileInput.parentElement.querySelector('.preview');
            const fileNameDisplay = fileInput.parentElement.querySelector('.file-name');
            if (preview && fileNameDisplay) {
                fileInput.addEventListener('change', () => {
                    const file = fileInput.files[0];
                    fileNameDisplay.textContent = file ? file.name : '';
                    if (file && file.type.startsWith('image/')) {
                        const reader = new FileReader();
                        reader.onload = function (e) {
                            preview.innerHTML = `<img src="${e.target.result}" alt="صورة معاينة">`;
                        };
                        reader.readAsDataURL(file);
                    } else {
                        preview.innerHTML = '';
                    }
                });
            }
        });
    }
    initFileUpload();

    /* User type toggle */
    const userTypeSelect = document.getElementById("userType");
    const sponsorFields = document.getElementById("sponsorFields");
    const supportedFields = document.getElementById("supportedFields");
    if (userTypeSelect && sponsorFields && supportedFields) {
        userTypeSelect.onchange = function () {
            if (this.value === "sponsor") {
                sponsorFields.style.display = "block";
                supportedFields.style.display = "none";
            } else {
                sponsorFields.style.display = "none";
                supportedFields.style.display = "block";
            }
        };
    }

    /* AOS Init */
    AOS.init();
});
