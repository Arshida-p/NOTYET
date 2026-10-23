/**
 * NOTYET - Shared Client-Side JavaScript
 * Controls responsive navigation, notification dismissals, and interactive UI micro-behaviors.
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Toggle
  const mobileToggle = document.getElementById('mobileMenuToggle');
  const navMenu = document.getElementById('navMenu');

  if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', () => {
      const isOpen = navMenu.classList.toggle('is-open');
      mobileToggle.setAttribute('aria-expanded', isOpen.toString());
      mobileToggle.textContent = isOpen ? '✕' : '☰';
    });
  }

  // 2. Alert Dismissal
  const alertCloses = document.querySelectorAll('.alert-close');
  alertCloses.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const alert = e.target.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        setTimeout(() => alert.remove(), 250);
      }
    });
  });

  // 3. Auto dismiss success alerts after 6 seconds
  const autoAlerts = document.querySelectorAll('.alert-success');
  autoAlerts.forEach(alert => {
    setTimeout(() => {
      if (alert && alert.parentElement) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        setTimeout(() => alert.remove(), 250);
      }
    }, 6000);
  });
});
