
const dialogo = document.getElementById('dialogo-excluir');
const abrirExclusao = document.getElementById('btn-excluir');
const cancelarExclusao = document.getElementById('btn-cancelar-exclusao');
const dialogoSenha = document.getElementById('dialogo-senha');
const abrirSenha = document.getElementById('btn-alterar-senha');

if (dialogo && abrirExclusao) {
  abrirExclusao.addEventListener('click', () => dialogo.showModal());
}

if (dialogo && cancelarExclusao) {
  cancelarExclusao.addEventListener('click', () => dialogo.close());
}

if (dialogoSenha && abrirSenha) {
  abrirSenha.addEventListener('click', () => dialogoSenha.showModal());
}

document.querySelectorAll('[data-open-delete]').forEach((botao) => {
  botao.addEventListener('click', () => {
    const alvo = document.getElementById(`dialogo-excluir-admin-${botao.dataset.openDelete}`);
    if (alvo) alvo.showModal();
  });
});

document.querySelectorAll('[data-close-dialog]').forEach((botao) => {
  botao.addEventListener('click', () => botao.closest('dialog')?.close());
});

document.querySelectorAll('dialog').forEach((dialog) => {
  if (dialog.dataset.reopen === 'true') dialog.showModal();
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
});