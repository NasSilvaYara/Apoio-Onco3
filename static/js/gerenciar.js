
/* ---------- Ações (aprovar, reativar, inativar) ---------- */

document.querySelector('#tabela tbody').addEventListener('click', (e) => {
  const botao = e.target.closest('[data-acao]');
  if (!botao) return;

  const linha = botao.closest('tr');
  const nome = linha.cells[0].textContent;

  if (botao.dataset.acao === 'inativar' && !confirm(`Inativar "${nome}"?`)) return;

  const novoStatus = botao.dataset.acao === 'aprovar' ? 'ativo' : 'desativado';
  linha.dataset.status = novoStatus;
  linha.querySelector('.badge').textContent = ROTULOS[novoStatus];
  filtrar();
});

filtrar();