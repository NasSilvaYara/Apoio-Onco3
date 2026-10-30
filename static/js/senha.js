document.querySelectorAll('.campo-senha').forEach((campo) => {
  const input = campo.querySelector('input');
  const botao = campo.querySelector('.ver-senha');
  const icone = botao.querySelector('i');

  botao.addEventListener('click', () => {
    const mostrando = input.type === 'text';
    input.type = mostrando ? 'password' : 'text';
    icone.className = mostrando ? 'ti ti-eye' : 'ti ti-eye-off';
    botao.setAttribute('aria-pressed', String(!mostrando));
    botao.setAttribute('aria-label', mostrando ? 'Mostrar senha' : 'Ocultar senha');
    input.focus();
  });
});