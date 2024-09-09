document.addEventListener('DOMContentLoaded', function () {
  const toggles = document.querySelectorAll('.menu-toggle');

  function toggleMenu(menu, state) {
    const subMenu = menu.nextElementSibling;

    if (state === 'open') {
      subMenu.style.display = 'block'; // Отображаем подменю
      subMenu.classList.add('open');
    } else {
      subMenu.classList.remove('open');
      subMenu.style.display = 'none'; // Скрываем подменю
    }
  }

  toggles.forEach(toggle => {
    const subMenu = toggle.nextElementSibling;
    const menuId = toggle.getAttribute('data-menu-id');
    const savedState = localStorage.getItem('menuState-' + menuId);

    // Если сохранено состояние "open", оставляем меню открытым
    if (savedState === 'open') {
      toggleMenu(toggle, 'open');
    }

    toggle.addEventListener('click', function () {
      const isOpen = subMenu.classList.contains('open');
      const newState = isOpen ? 'closed' : 'open';

      // Сохраняем состояние в localStorage
      localStorage.setItem('menuState-' + menuId, newState);

      // Переключаем меню
      toggleMenu(toggle, newState);
    });
  });
});
