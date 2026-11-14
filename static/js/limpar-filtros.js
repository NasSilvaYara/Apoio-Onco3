const formFiltros = document.getElementById('filtro-busca-form');
const botaoLimparFiltros = document.querySelector('[data-limpar-filtros]');

if (formFiltros && botaoLimparFiltros) {
  botaoLimparFiltros.addEventListener('click', () => {
    Array.from(formFiltros.elements).forEach((campo) => {
      if (campo instanceof HTMLInputElement) {
        if (campo.type === 'checkbox' || campo.type === 'radio') {
          campo.checked = false;
        } else if (campo.type !== 'hidden' && campo.type !== 'submit' && campo.type !== 'button') {
          campo.value = '';
        }
      } else if (campo instanceof HTMLSelectElement) {
        campo.selectedIndex = 0;
      }
    });

    formFiltros.requestSubmit();
  });
}
