
const dialogo = document.getElementById('dialogo-excluir');
const abrirExclusao = document.getElementById('btn-excluir');
const cancelarExclusao = document.getElementById('btn-cancelar-exclusao');

if (dialogo && abrirExclusao) {
  abrirExclusao.addEventListener('click', () => dialogo.showModal());
}

if (dialogo && cancelarExclusao) {
  cancelarExclusao.addEventListener('click', () => dialogo.close());
}

if (dialogo) {
  dialogo.addEventListener('click', (e) => {
    if (e.target === dialogo) dialogo.close();
  });
}