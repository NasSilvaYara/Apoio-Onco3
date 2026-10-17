/* ---------- Gerenciamento dos Menus de Filtro ---------- */
const botoesFiltro = document.querySelectorAll('.filter-btn');

function fecharTodosFiltros() {
    botoesFiltro.forEach(btn => {
        btn.setAttribute('aria-expanded', 'false');
        const menuId = btn.getAttribute('aria-controls');
        const menuEl = document.getElementById(menuId);
        if (menuEl) menuEl.hidden = true;
    });
}

botoesFiltro.forEach(btn => {
    btn.addEventListener('click', (e) => {
        e.stopPropagation(); // Evita fechar imediatamente pelo listener global
        const menuId = btn.getAttribute('aria-controls');
        const menuEl = document.getElementById(menuId);
        
        const estaAberto = !menuEl.hidden;

        // Fecha todos os outros menus antes de abrir o atual
        fecharTodosFiltros();

        if (!estaAberto) {
            menuEl.hidden = false;
            btn.setAttribute('aria-expanded', 'true');
        }
    });
});

// Fecha os menus se clicar em qualquer lugar fora deles
document.addEventListener('click', (e) => {
    if (!e.target.closest('.filtro-dropdown-container')) {
        fecharTodosFiltros();
    }
});

// Fecha com a tecla Esc
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        fecharTodosFiltros();
    }
});