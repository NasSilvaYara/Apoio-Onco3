

const dialogo = document.getElementById('dialogo-editar');
const campoEditar = document.getElementById('nome-editar');
const idEditar = document.getElementById('id-editar');

// Clique no lápis: abre o modal com o nome e o id da categoria da linha
document.querySelector('#tabela-categorias tbody').addEventListener('click', (e) => {
  const botao = e.target.closest('.btn-editar');
  if (!botao) return;

  const linha = botao.closest('tr');
  idEditar.value = linha.dataset.id || '';
  campoEditar.value = linha.querySelector('.nome-categoria').textContent.trim();

  dialogo.showModal();
  campoEditar.select();
});

// Fecha o modal: botão Cancelar, tecla Esc (nativa) ou clique no fundo escuro
document.getElementById('btn-cancelar-edicao').addEventListener('click', () => dialogo.close());

dialogo.addEventListener('click', (e) => {
  if (e.target === dialogo) dialogo.close();
});

document.querySelector('#tabela-categorias tbody').addEventListener('change', (e) => {
  if (e.target.matches('.switch')) e.target.form.requestSubmit();
});

document.addEventListener('submit', (e) => {
  const form = e.target.closest('form[data-confirm]');
  if (form && !confirm(form.dataset.confirm)) e.preventDefault();
});