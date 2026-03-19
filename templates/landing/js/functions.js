$(function(){
    $(".nav-link").click(function(){
      $(".nav-link").removeClass("active");
      $(this).addClass("active");
    });
});
/*---------- modal yateem --------------*/
const modallY = document.getElementById("myModalyateem");
const btnnn = document.getElementById("openModalyateem");
const spannn = document.querySelector(".closeee");
btnnn.onclick = function() {
  modallY.style.display = "block";
}
spannn.onclick = function() {
  modallY.style.display = "none";
}
window.onclick = function(event) {
  if (event.target == modal) {
    modallY.style.display = "none";
  }
}

/*---------- modal login and register --------------*/


  /* login */
        const modal = document.getElementById("myModal");
        const btn = document.getElementById("openModalBtn");
        const span = document.querySelector(".close");

        btn.onclick = function() {
        modal.style.display = "block";
        }

        span.onclick = function() {
        modal.style.display = "none";
        }

        window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
        }
        /*------*/
        const modd = document.getElementById("myModalRegister");
        const bbttn = document.getElementById("signupLink");
        const ssppan = document.querySelector(".close");

        bbttn.onclick = function() {
        modd.style.display = "block";
        modal.style.display= "none";
        }

        ssppan.onclick = function() {
        modd.style.display = "none";
        }

        window.onclick = function(event) {
        if (event.target == modal) {
            modd.style.display = "none";
        }
        }
        /* signup */
        const modall = document.getElementById("myModalRegister");
        const mod = document.getElementById("myModal");
        const bbtn = document.getElementById("loginLink");
        const sspan = document.querySelector(".close");

        bbtn.onclick = function() {
        mod.style.display = "block";
        modall.style.display= "none"
        }

        sspan.onclick = function() {
        mod.style.display = "none";
        }

        window.onclick = function(event) {
        if (event.target == modal) {
            mod.style.display = "none";
        }
        }
        const btnn = document.getElementById("openModalBtnRegister");
        const spann = document.querySelector(".closee");

        btnn.onclick = function() {
        modall.style.display = "block";
        }

        spann.onclick = function() {
        modall.style.display = "none";
        }

        window.onclick = function(event) {
        if (event.target == modal) {
            modall.style.display = "none";
        }
}
/*------------ upload image ---------------*/
 const fileInput = document.getElementById('file-input');
    const preview = document.getElementById('preview');
    const fileNameDisplay = document.getElementById('file-name');

    fileInput.addEventListener('change', () => {
      const file = fileInput.files[0];
      fileNameDisplay.textContent = file ? file.name : '';

      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
          preview.innerHTML = `<img src="${e.target.result}" alt="صورة معاينة">`;
        };
        reader.readAsDataURL(file);
      } else {
        preview.innerHTML = '';
      }
});
  // Card click animation
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('click', function () {
                this.classList.remove('bounce-animation');
                void this.offsetWidth;
                this.classList.add('bounce-animation');
            });
        });

        // Navigation background on scroll
        window.addEventListener('scroll', function () {
            const nav = document.querySelector('nav');
            if (window.scrollY > 50) {
                nav.classList.add('scrolled');
            } else {
                nav.classList.remove('scrolled');
            }
        });
const userTypeSelect = document.getElementById("userType");
const sponsorFields = document.getElementById("sponsorFields");
const supportedFields = document.getElementById("supportedFields");

// تغيير الحقول بناءً على نوع المستخدم
userTypeSelect.onchange = function() {
  updateFields(this.value);
}

function updateFields(userType) {
  if (userType === "sponsor") {
    sponsorFields.style.display = "block";
    supportedFields.style.display = "none";
  } else {
    sponsorFields.style.display = "none";
    supportedFields.style.display = "block";
  }
}
