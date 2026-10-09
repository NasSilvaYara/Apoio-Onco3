
const dialogo = document.getElementById('dialogo-excluir');

document.getElementById('btn-excluir')
  .addEventListener('click', () => dialogo.showModal());

document.getElementById('btn-cancelar-exclusao')
  .addEventListener('click', () => dialogo.close());


dialogo.addEventListener('click', (e) => {
  if (e.target === dialogo) dialogo.close();
});