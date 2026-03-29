// ==========================================
// 1. Sidebar & Mobile Menu Logic
// ==========================================
document.addEventListener("DOMContentLoaded", function () {
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  const mobileMenuToggle = document.getElementById('mobileMenuToggle'); // تم تعريفه لحل الخطأ
  const body = document.body;

  if (sidebarToggle && sidebar) {
    const overlay = document.createElement("div");
    overlay.className = "overlay";
    body.appendChild(overlay);

    function toggleSidebar() {
      sidebar.classList.toggle("active");
      overlay.classList.toggle("active");
      const icon = sidebarToggle.querySelector("i");
      if (icon) {
        if (sidebar.classList.contains("active")) {
          icon.classList.remove("fa-bars");
          icon.classList.add("fa-times");
        } else {
          icon.classList.remove("fa-times");
          icon.classList.add("fa-bars");
        }
      }
    }

    sidebarToggle.addEventListener("click", toggleSidebar);
    overlay.addEventListener("click", toggleSidebar);

    const menuItems = document.querySelectorAll(".menu-item");
    menuItems.forEach((item) => {
      item.addEventListener("click", function () {
        if (window.innerWidth <= 840 && sidebar.classList.contains("active")) {
          toggleSidebar();
        }
      });
    });

    window.addEventListener("resize", function () {
      if (window.innerWidth > 840) {
        sidebar.classList.remove("active");
        overlay.classList.remove("active");
        const icon = sidebarToggle.querySelector("i");
        if (icon) {
          icon.classList.remove("fa-times");
          icon.classList.add("fa-bars");
        }
      }
      
      // دمج كود الـ Resize الثاني لحل خطأ mobileMenuToggle
      if (window.innerWidth > 768) {
        sidebar.classList.remove('active');
        if (mobileMenuToggle) {
          mobileMenuToggle.innerHTML = '<i class="fas fa-bars"></i>';
        }
      }
    });
  }
});

// ==========================================
// 2. Counters Animation
// ==========================================
document.addEventListener('DOMContentLoaded', function () {
  const counters = document.querySelectorAll('.counter');
  if (counters.length > 0) {
    const duration = 2000;
    function animateCounter(counter, target) {
      let start = 0;
      const increment = target / (duration / 16);
      const updateCounter = () => {
        start += increment;
        if (start < target) {
          counter.textContent = Math.floor(start);
          requestAnimationFrame(updateCounter);
        } else {
          counter.textContent = target;
          counter.classList.add('finished');
        }
      };
      updateCounter();
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const counter = entry.target;
          const target = parseInt(counter.getAttribute('data-target'));
          animateCounter(counter, target);
          observer.unobserve(counter);
        }
      });
    }, { threshold: 0.5 });

    counters.forEach(counter => observer.observe(counter));
  }
});

// ==========================================
// 3. Menu Links Active State
// ==========================================
document.addEventListener('DOMContentLoaded', function () {
  const menuLinks = document.querySelectorAll('.menu a');
  menuLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
      });
    });
  });
});

// ==========================================
// 4. Modals (Popups) Handling - Safe Mode
// ==========================================
document.addEventListener('DOMContentLoaded', function () {
  
  // دالة مساعدة لفتح وإغلاق النوافذ بأمان
  function setupModal(modalId, btnClassOrId, closeSelector, isId = true) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    const btns = isId ? [document.getElementById(btnClassOrId)] : document.querySelectorAll(btnClassOrId);
    const closeBtns = document.querySelectorAll(closeSelector);

    if (btns.length > 0 && btns[0] !== null) {
      btns.forEach(btn => {
        if(btn) {
          btn.addEventListener('click', function(e) {
            e.preventDefault();
            modal.style.display = 'flex'; // أو block حسب الـ CSS الخاص بك
          });
        }
      });
    }

    if (closeBtns.length > 0) {
      closeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
          modal.style.display = 'none';
        });
      });
    }

    window.addEventListener('click', function(event) {
      if (event.target === modal) {
        modal.style.display = 'none';
      }
    });
    
    // منع الإغلاق عند الضغط داخل النافذة
    const content = modal.querySelector('.popup-content') || modal.querySelector('.modal-dialog');
    if (content) {
        content.addEventListener('click', function(e) { e.stopPropagation(); });
        content.addEventListener('mousedown', function(e) { e.stopPropagation(); });
    }
  }

  // تهيئة جميع النوافذ (لن يظهر خطأ إذا لم تكن موجودة في الصفحة)
  setupModal('editPopup', 'editBtn', '.close-btn', true);
  setupModal('documentModal', '.btn-view', '.close-modal', false);
  setupModal('myModal', '.btn-download', '.close, .cancel-btn', false);
  setupModal('showguarantee', '.show-guarantee', '.close', false);
  setupModal('dynamicModal', '.notification-detailes', '.close-modal', false);
  setupModal('paymentModal', '.show-guarantee', '.close', false);
  setupModal('sponsorModal', '.sponsor-btn', '#close', false);
  setupModal('ShowGuarantee', '.show-guarantee', '.close-modal', false);
});

// ==========================================
// 5. Notifications & Profile Panels
// ==========================================
document.addEventListener('DOMContentLoaded', function () {
  const bellIcon = document.getElementById('bellIcon');
  const notificationPanel = document.getElementById('notificationPanel');
  const profileIcon = document.getElementById('profileIcon');
  const profilePanel = document.getElementById('profilePanel');

  if (bellIcon && notificationPanel) {
    bellIcon.addEventListener('click', function (e) {
      e.stopPropagation();
      notificationPanel.classList.toggle('show');
      if (profilePanel) profilePanel.classList.remove('show');
    });
    notificationPanel.addEventListener('click', function (e) { e.stopPropagation(); });
  }

  if (profileIcon && profilePanel) {
    profileIcon.addEventListener('click', function (e) {
      e.stopPropagation();
      profilePanel.classList.toggle('show');
      if (notificationPanel) notificationPanel.classList.remove('show');
    });
    profilePanel.addEventListener('click', function (e) { e.stopPropagation(); });
  }

  document.addEventListener('click', function () {
    if (notificationPanel) notificationPanel.classList.remove('show');
    if (profilePanel) profilePanel.classList.remove('show');
  });

  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function () {
      alert('تم تسجيل الخروج بنجاح');
    });
  }
});

// ==========================================
// 6. Charts Initialization (Safe Mode)
// ==========================================
document.addEventListener('DOMContentLoaded', function () {
  const canvas1 = document.getElementById('chart1');
  if (canvas1) {
    const ctx1 = canvas1.getContext('2d');
    new Chart(ctx1, {
      type: 'line',
      data: {
        labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
        datasets: [{
          label: 'عدد الأيتام المكفولين',
          data: [50, 30, 90, 60, 150, 120],
          borderColor: '#177772',
          backgroundColor: 'rgba(76, 175, 80, 0.2)',
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'top' } },
        scales: { y: { beginAtZero: true } }
      }
    });
  }

  const canvas2 = document.getElementById('chart2');
  if (canvas2) {
    const ctx2 = canvas2.getContext('2d');
    new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['الأيتام', 'الكافلين', 'مكفولين', 'متاحين'],
        datasets: [{
          label: 'الإحصائيات',
          data: [377, 220, 320, 100],
          backgroundColor: ['#2b726e', '#8b9798', '#8b9798', '#2b726e'],
        }]
      },
      options: {
        responsive: true,
        scales: { y: { beginAtZero: true } }
      }
    });
  }
});

// ==========================================
// 7. Registration User Type Toggle
// ==========================================
document.addEventListener('DOMContentLoaded', function () {
  const userTypeSelect = document.getElementById("userType");
  const sponsorFields = document.getElementById("sponsorFields");
  const supportedFields = document.getElementById("supportedFields");

  function toggleRequired(container, isRequired) {
    if (!container) return;
    const inputs = container.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="number"]');
    inputs.forEach(input => {
      input.required = isRequired;
    });
  }

  if (userTypeSelect) {
    toggleRequired(sponsorFields, true);
    toggleRequired(supportedFields, false);

    userTypeSelect.addEventListener('change', function () {
      if (this.value === "sponsor") {
        if(sponsorFields) sponsorFields.style.display = "block";
        if(supportedFields) supportedFields.style.display = "none";
        toggleRequired(sponsorFields, true);
        toggleRequired(supportedFields, false);
      } else {
        if(sponsorFields) sponsorFields.style.display = "none";
        if(supportedFields) supportedFields.style.display = "block";
        toggleRequired(sponsorFields, false);
        toggleRequired(supportedFields, true);
      }
    });
  }
});