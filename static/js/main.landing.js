$(function () {
    $(".nav-link").click(function () {
        $(".nav-link").removeClass("active");
        $(this).addClass("active");
    });
});

/*---------- Back to Top Button --------------*/
const backToTopButton = document.getElementById('back-to-top');
if (backToTopButton) {
    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            backToTopButton.style.display = 'block';
        } else {
            backToTopButton.style.display = 'none';
        }
    });
    backToTopButton.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/*---------- Modals Setup --------------*/
// Get Modals
const modalYateem = document.getElementById("myModalyateem");
const modalLogin = document.getElementById("myModal");
const modalRegister = document.getElementById("myModalRegister");

// Get Buttons that open them
const btnOpenYateem = document.getElementById("openModalyateem");
const btnOpenLogin = document.getElementById("openModalBtn");
const btnOpenRegister = document.getElementById("openModalBtnRegister");

// Get Links inside modals that switch between them
const linkToSignup = document.getElementById("signupLink");
const linkToLogin = document.getElementById("loginLink");

// Get Close 'X' buttons
const closeYateem = document.querySelector("#myModalyateem .closeee");
const closeLogin = document.querySelector("#myModal .close");
const closeRegister = document.querySelector("#myModalRegister .closee");

// 1. Yateem Modal Logic
if (btnOpenYateem && modalYateem) {
    btnOpenYateem.onclick = function (e) {
        e.preventDefault();
        modalYateem.style.display = "block";
    }
    if (closeYateem) {
        closeYateem.onclick = function () {
            modalYateem.style.display = "none";
        }
    }
}

// 2. Login Modal Logic
if (btnOpenLogin && modalLogin) {
    btnOpenLogin.onclick = function (e) {
        e.preventDefault();
        modalLogin.style.display = "block";
    }
    if (closeLogin) {
        closeLogin.onclick = function () {
            modalLogin.style.display = "none";
        }
    }
}

// 3. Register Modal Logic
if (btnOpenRegister && modalRegister) {
    btnOpenRegister.onclick = function (e) {
        e.preventDefault();
        modalRegister.style.display = "block";
    }
    if (closeRegister) {
        closeRegister.onclick = function () {
            modalRegister.style.display = "none";
        }
    }
}

// 4. Switch from Login to Register
if (linkToSignup) {
    linkToSignup.onclick = function (e) {
        e.preventDefault();
        modalLogin.style.display = "none";
        modalRegister.style.display = "block";
    }
}

// 5. Switch from Register to Login
if (linkToLogin) {
    linkToLogin.onclick = function (e) {
        e.preventDefault();
        modalRegister.style.display = "none";
        modalLogin.style.display = "block";
    }
}

// 6. SINGLE window.onclick to handle closing ALL modals when clicking outside
window.onclick = function (event) {
    if (event.target == modalYateem) {
        modalYateem.style.display = "none";
    }
    if (event.target == modalLogin) {
        modalLogin.style.display = "none";
    }
    if (event.target == modalRegister) {
        modalRegister.style.display = "none";
    }
}

/*------------ Upload Image Preview ---------------*/
const fileInput = document.getElementById('file-input');
const preview = document.getElementById('preview');
const fileNameDisplay = document.getElementById('file-name');

if (fileInput) {
    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (fileNameDisplay) {
            fileNameDisplay.textContent = file ? file.name : '';
        }

        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function (e) {
                if (preview) {
                    preview.innerHTML = `<img src="${e.target.result}" alt="صورة معاينة" style="max-width:100%; border-radius:8px;">`;
                }
            };
            reader.readAsDataURL(file);
        } else {
            if (preview) {
                preview.innerHTML = '';
            }
        }
    });
}

/*------------ User Type Select (Register Modal) ---------------*/
const userTypeSelect = document.getElementById("userType");
const sponsorFields = document.getElementById("sponsorFields");
const supportedFields = document.getElementById("supportedFields");

if (userTypeSelect) {
    userTypeSelect.onchange = function () {
        if (this.value === "sponsor") {
            if(sponsorFields) sponsorFields.style.display = "block";
            if(supportedFields) supportedFields.style.display = "none";
        } else {
            if(sponsorFields) sponsorFields.style.display = "none";
            if(supportedFields) supportedFields.style.display = "block";
        }
    }
}