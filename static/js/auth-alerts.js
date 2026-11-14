const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('erro-login');
const loginMessages = document.querySelectorAll('#mensagens-login [data-swal-message]');

async function mostrarAlertaLogin(mensagem, titulo = 'Não foi possível entrar') {
  if (!window.Swal) {
    if (loginError) {
      loginError.textContent = mensagem;
      loginError.hidden = false;
    }
    console.error('SweetAlert2 não foi carregado; erro de login:', mensagem);
    return;
  }

  document.activeElement?.blur();
  await window.Swal.fire({
    icon: 'error',
    title: titulo,
    text: mensagem,
    confirmButtonText: 'Entendi',
    returnFocus: false,
  });
}

const mensagemServidor = [...loginMessages]
  .map((item) => item.textContent.trim())
  .filter(Boolean)
  .join('\n');
if (mensagemServidor) {
  mostrarAlertaLogin(mensagemServidor);
}

if (loginForm) {
  loginForm.addEventListener('submit', async (event) => {
    const email = loginForm.elements.email;
    const senha = loginForm.elements.senha;
    let campoInvalido = null;
    let mensagem = '';

    if (!email.value.trim()) {
      campoInvalido = email;
      mensagem = 'Informe seu e-mail.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim())) {
      campoInvalido = email;
      mensagem = 'O e-mail informado não está em um formato válido.';
    } else if (!senha.value) {
      campoInvalido = senha;
      mensagem = 'Informe sua senha para entrar.';
    }

    if (campoInvalido) {
      event.preventDefault();
      await mostrarAlertaLogin(mensagem, 'Confira os dados de acesso');
      campoInvalido.focus();
    }
  });
}
