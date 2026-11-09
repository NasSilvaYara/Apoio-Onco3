

const dialogo = document.getElementById('dialogo-editar');
const campoEditar = document.getElementById('nome-editar');
const idEditar = document.getElementById('id-editar');
const dialogoExcluir = document.getElementById('dialogo-excluir-categoria');
const idExcluir = document.getElementById('id-excluir-categoria');

if (dialogo.dataset.reopen === 'true') dialogo.showModal();

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

document.querySelector('#tabela-categorias tbody').addEventListener('click', (event) => {
  const botao = event.target.closest('[data-excluir-categoria]');
  if (!botao || !dialogoExcluir) return;

  idExcluir.value = botao.dataset.excluirCategoria;
  dialogoExcluir.showModal();
});

document.querySelector('[data-cancelar-exclusao]').addEventListener('click', () => {
  dialogoExcluir.close();
});

dialogoExcluir.addEventListener('click', (event) => {
  if (event.target === dialogoExcluir) dialogoExcluir.close();
});