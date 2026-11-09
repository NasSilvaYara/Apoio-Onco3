const toggle = document.querySelector('[data-sidebar-toggle]');
const backdrop = document.querySelector('[data-sidebar-close]');

if (toggle && backdrop) {
  const closeMenu = () => {
    document.body.classList.remove('dashboard-sidebar-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', toggle.dataset.labelOpen);
    backdrop.hidden = true;
  };

  toggle.addEventListener('click', () => {
    const isOpen = document.body.classList.toggle('dashboard-sidebar-open');
    toggle.setAttribute('aria-expanded', String(isOpen));
    toggle.setAttribute(
      'aria-label',
      isOpen ? toggle.dataset.labelClose : toggle.dataset.labelOpen,
    );
    backdrop.hidden = !isOpen;
  });

  backdrop.addEventListener('click', closeMenu);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') closeMenu();
  });

  document.querySelectorAll('.sidebar .menu-item[href]').forEach((item) => {
    item.addEventListener('click', closeMenu);
  });
}
