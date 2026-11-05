const modalSair = document.getElementById('modal-sair');
const abrirSair = document.getElementById('abrir-sair');
const cancelarSair = document.getElementById('cancelar-sair');

abrirSair.addEventListener('click', () => modalSair.showModal());
cancelarSair.addEventListener('click', () => modalSair.close());

// clicar fora da caixinha (no fundo escuro) também fecha
modalSair.addEventListener('click', (e) => {
  if (e.target === modalSair) modalSair.close();
});