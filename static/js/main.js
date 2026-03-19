document.addEventListener("DOMContentLoaded", function () {
  // Elements
  const sidebarToggle = document.getElementById("sidebar-toggle");
  const sidebar = document.getElementById("sidebar");
  const body = document.body;

  // Create overlay element for mobile
  const overlay = document.createElement("div");
  overlay.className = "overlay";
  body.appendChild(overlay);

  // Toggle sidebar function
  function toggleSidebar() {
    sidebar.classList.toggle("active");
    overlay.classList.toggle("active");

    // Toggle burger icon
    const icon = sidebarToggle.querySelector("i");
    if (sidebar.classList.contains("active")) {
      icon.classList.remove("fa-bars");
      icon.classList.add("fa-times");
    } else {
      icon.classList.remove("fa-times");
      icon.classList.add("fa-bars");
    }
  }

  // Event listeners
  sidebarToggle.addEventListener("click", toggleSidebar);
  overlay.addEventListener("click", toggleSidebar);

  // Close sidebar when clicking on menu items on mobile
  const menuItems = document.querySelectorAll(".menu-item");
  menuItems.forEach((item) => {
    item.addEventListener("click", function () {
      if (window.innerWidth <= 840 && sidebar.classList.contains("active")) {
        toggleSidebar();
      }
    });
  });

  // Handle window resize
  window.addEventListener("resize", function () {
    // If window is resized larger than mobile breakpoint, reset sidebar
    if (window.innerWidth > 840) {
      sidebar.classList.remove("active");
      overlay.classList.remove("active");
      const icon = sidebarToggle.querySelector("i");
      icon.classList.remove("fa-times");
      icon.classList.add("fa-bars");
    }
  });
});


document.addEventListener('DOMContentLoaded', function () {

  function handleResize() {
    if (window.innerWidth > 768) {
      sidebar.classList.remove('active');
      if (mobileMenuToggle) {
        mobileMenuToggle.innerHTML = '<i class="fas fa-bars"></i>';
      }
    }
  }

  window.addEventListener('resize', handleResize);
  handleResize();
});
document.addEventListener('DOMContentLoaded', function () {
  const counters = document.querySelectorAll('.counter');
  const duration = 2000; // مدة العد بالمللي ثانية

  function animateCounter(counter, target) {
    let start = 0;
    const increment = target / (duration / 16); // 60 إطار في الثانية

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

  // بدء العد عند ظهور العنصر في الشاشة
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

  counters.forEach(counter => {
    observer.observe(counter);
  });
});

document.addEventListener('DOMContentLoaded', function () {
  const menuLinks = document.querySelectorAll('.menu a');

  menuLinks.forEach(link => {
    link.addEventListener('click', function (e) {
      // إزالة الكلاس النشط من جميع العناصر
      document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
      });
    });
  });




/*  أوامر تنفيذ تعديل بيانات كفالة اليتيم عند النقر على زر تعديل البيانات في صفحة عرض اليتيم    */
document.addEventListener('DOMContentLoaded', function () {
  // الحصول على العناصر
  const editBtn = document.getElementById('editBtn');
  const editPopup = document.getElementById('editPopup');
  const closeBtn = document.querySelector('.close-btn');

  // عند النقر على زر التعديل
  editBtn.addEventListener('click', function () {
    editPopup.style.display = 'flex';
  });

  // عند النقر على زر الإغلاق
  closeBtn.addEventListener('click', function () {
    editPopup.style.display = 'none';
  });

  // عند النقر خارج النافذة المنبثقة
  window.addEventListener('click', function (event) {
    if (event.target === editPopup) {
      editPopup.style.display = 'none';
    }
  });

  // منع إغلاق النافذة عند النقر داخلها
  editPopup.querySelector('.popup-content').addEventListener('click', function (e) {
    e.stopPropagation();
  });
});


/*     ************************     */

/* تنفيذ أمر عرض البيانات عند النقر على زر عرض البيانات  في صفحة عرض اليتيم */

document.addEventListener('DOMContentLoaded', function () {
  // الحصول على العناصر
  const modal = document.getElementById('documentModal');
  const closeBtn = document.querySelector('.close-modal');
  const viewButtons = document.querySelectorAll('.btn-view');

  // عند النقر على زر عرض
  viewButtons.forEach(button => {
    button.addEventListener('click', function () {
      modal.style.display = 'flex';
    });
  });

  // عند النقر على زر الإغلاق
  closeBtn.addEventListener('click', function () {
    modal.style.display = 'none';
  });

  // عند النقر خارج النافذة
  window.addEventListener('click', function (event) {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });

});

/*    ***********************************************    */


/*     تنفيذ أمر تحميل عند النقر على زر تحميل في صفحة عرض اليتيم  */
document.addEventListener('DOMContentLoaded', function () {
  // الحصول على العناصر
  const modal = document.getElementById('myModal');
  const btns = document.querySelectorAll('.btn-download');
  const span = document.querySelector('.close');
  const cancelBtn = document.querySelector('.cancel-btn');

  // عند النقر على الزر، تظهر النافذة

  btns.forEach(btn => {
    btn.addEventListener('click', function () {
      modal.style.display = 'flex';
    });
  });

  // عند النقر على (x)، تغلق النافذة
  span.onclick = function () {
    modal.style.display = 'none';
  }

  // عند النقر على زر الإلغاء
  cancelBtn.onclick = function () {
    modal.style.display = 'none';
  }

  // عند النقر خارج النافذة، تغلق
  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = 'none';
    }
  }
});

/*    ********************************    */
/*      عند النقر على زر عرض الكفالة في صفحة ادارة الكفالات      */

document.addEventListener('DOMContentLoaded', function () {
  // العناصر المطلوبة
  const modal = document.getElementById("showguarantee");
  const closeBtn = document.querySelector(".close");
  const detailBtns = document.querySelectorAll(".show-guarantee");

  // لكل زر تفاصيل
  detailBtns.forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      modal.style.display = "block";
    });
  });

  // إغلاق النافذة
  closeBtn.addEventListener('click', function () {
    modal.style.display = "none";
  });

  // إغلاق عند النقر خارج النافذة
  window.addEventListener('click', function (e) {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });
});


/* ******************************************** */

/*      عند النقر على زر التفاصيل في صفحة الإشعارات         */

document.addEventListener('DOMContentLoaded', function () {
  const modal = document.getElementById('dynamicModal');
  const detailButtons = document.querySelectorAll('.notification-detailes');

  // لكل زر تفاصيل
  detailButtons.forEach(button => {
    button.addEventListener('click', function (e) {
      e.preventDefault();
      // إظهار النافذة المنبثقة
      modal.style.display = 'block';
    });
  });

  // إغلاق النافذة
  document.querySelector('.close-modal').addEventListener('click', function () {
    modal.style.display = 'none';
  });

  // إغلاق عند النقر خارج النافذة
  window.addEventListener('click', function (event) {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });
});
/*************************************************************** */
/*      دالة فتح نافذة المدفوعات      */
document.addEventListener('DOMContentLoaded', function () {
  // العناصر المطلوبة
  const modal = document.getElementById("paymentModal");
  const closeBtn = document.querySelector(".close");
  const detailBtns = document.querySelectorAll(".show-guarantee");

  // لكل زر تفاصيل
  detailBtns.forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      modal.style.display = "block";
    });
  });

  // إغلاق النافذة
  closeBtn.addEventListener('click', function () {
    modal.style.display = "none";
  });

  // إغلاق عند النقر خارج النافذة
  window.addEventListener('click', function (e) {
    if (e.target === modal) {
      modal.style.display = "none";
    }
  });
});





/*        النافذة المنبثقة الخاصة بالضغط على زر أكفل الأن     */
document.addEventListener('DOMContentLoaded', function () {
  // Get the modal and close button
  const modal = document.getElementById("sponsorModal");
  const closeBtn = document.getElementById("close");

  // Get all sponsor buttons (يمكن إضافة class مشترك لجميع أزرار الكفالة)
  const sponsorBtns = document.querySelectorAll(".sponsor-btn");

  // When any sponsor button is clicked, open the modal
  sponsorBtns.forEach(btn => {
    btn.onclick = function () {
      modal.style.display = "block";
    };
  });

  // When the user clicks on close button (x), close the modal
  closeBtn.onclick = function () {
    modal.style.display = "none";
  };

  // When the user clicks anywhere outside of the modal, close it
  window.onclick = function (event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  };
});

/*      عند النقر على زر عرض الكفالة في صفحة ادارة الكفالات في لوحة تحكم الأدمن     */

document.addEventListener('DOMContentLoaded', function () {
  const modal = document.getElementById('ShowGuarantee');
  const detailButtons = document.querySelectorAll('.show-guarantee');

  // لكل زر تفاصيل
  detailButtons.forEach(button => {
    button.addEventListener('click', function (e) {
      e.preventDefault();
      // إظهار النافذة المنبثقة
      modal.style.display = 'block';
    });
  });

  // إغلاق النافذة
  document.querySelector('.close-modal').addEventListener('click', function () {
    modal.style.display = 'none';
  });

  // إغلاق عند النقر خارج النافذة
  window.addEventListener('click', function (event) {
    if (event.target === modal) {
      modal.style.display = 'none';
    }
  });
});


/*******         bill notfication  */
// عرض/إخفاء لوحة الإشعارات عند النقر على الجرس
document.addEventListener('DOMContentLoaded', function () {
  // تهيئة الجرس والإشعارات
  const bellIcon = document.getElementById('bellIcon');
  const notificationPanel = document.getElementById('notificationPanel');

  if (bellIcon && notificationPanel) {
    bellIcon.addEventListener('click', function (e) {
      e.stopPropagation();
      notificationPanel.classList.toggle('show');
      // إغلاق لوحة الملف الشخصي إذا كانت مفتوحة
      const profilePanel = document.getElementById('profilePanel');
      if (profilePanel) profilePanel.classList.remove('show');
    });
  }

  // تهيئة صورة الملف الشخصي
  const profileIcon = document.getElementById('profileIcon');
  const profilePanel = document.getElementById('profilePanel');

  if (profileIcon && profilePanel) {
    profileIcon.addEventListener('click', function (e) {
      e.stopPropagation();
      profilePanel.classList.toggle('show');
      // إغلاق لوحة الإشعارات إذا كانت مفتوحة
      if (notificationPanel) notificationPanel.classList.remove('show');
    });
  }

  // إغلاق اللوحات عند النقر خارجها
  document.addEventListener('click', function () {
    if (notificationPanel) notificationPanel.classList.remove('show');
    if (profilePanel) profilePanel.classList.remove('show');
  });

  // منع إغلاق اللوحات عند النقر عليها
  if (notificationPanel) {
    notificationPanel.addEventListener('click', function (e) {
      e.stopPropagation();
    });
  }

  if (profilePanel) {
    profilePanel.addEventListener('click', function (e) {
      e.stopPropagation();
    });
  }

  // زر تسجيل الخروج
  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', function () {
      // هنا يمكنك إضافة وظيفة تسجيل الخروج الفعلية
      alert('تم تسجيل الخروج بنجاح');
      // window.location.href = 'logout.php'; // مثال لتوجيه إلى صفحة تسجيل الخروج
    });
  }
});
/**************************************** */
const ctx1 = document.getElementById('chart1').getContext('2d');
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
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      }
    }
  }
});

const ctx2 = document.getElementById('chart2').getContext('2d');
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
    scales: {
      y: {
        beginAtZero: true
      }
    }
  }
})
});

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

    userTypeSelect.onchange = function () {
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
    }
}
