// true  = não envia ao servidor e mostra a tela "Cadastro enviado!"
// false = envia o formulário por POST para a view do Django
const SO_FRONT = true;

const form = document.getElementById('cadastro');
const etapas = [...document.querySelectorAll('.etapa')];
const passos = [...document.querySelectorAll('.passo')];
const btnVoltar = document.getElementById('voltar');
const btnAvancar = document.getElementById('avancar');
const tituloEtapa = document.getElementById('titulo-etapa');
const tituloBanner = document.getElementById('titulo-banner');

const TITULOS = [
  'Validar o CNPJ',
  'Dados da instituição',
  'Endereço da instituição',
  'Dados de contato',
  'Dados de acesso',
  'Confira os dados antes de enviar',
];

let atual = 0;

/* ---------- Navegação ---------- */

function mostrar(i) {
  atual = i;
  etapas.forEach((e, n) => e.classList.toggle('ativa', n === i));
  passos.forEach((p, n) => {
    p.classList.toggle('feito', n < i);
    p.classList.toggle('atual', n === i);
    if (n === i) p.setAttribute('aria-current', 'step');
    else p.removeAttribute('aria-current');
  });
  tituloEtapa.textContent = TITULOS[i];
  tituloBanner.textContent = TITULOS[i];
  btnVoltar.hidden = i === 0;
  btnAvancar.textContent = i === etapas.length - 1 ? 'Enviar cadastro' : 'Avançar';
  if (i === etapas.length - 1) montarRevisao();

  const primeiro = etapas[i].querySelector('input, select, textarea');
  if (primeiro) primeiro.focus();
}

function avancar() {
  if (!validar(atual)) return;
  if (atual < etapas.length - 1) {
    mostrar(atual + 1);
  } else if (SO_FRONT) {
    form.hidden = true;
    document.getElementById('passos').hidden = true;
    tituloEtapa.hidden = true;
    document.getElementById('rodape-login').hidden = true;
    document.getElementById('sucesso').hidden = false;
    tituloBanner.textContent = 'Obrigada por fazer parte!';
  } else {
    form.submit();
  }
}

btnAvancar.addEventListener('click', avancar);
btnVoltar.addEventListener('click', () => atual > 0 && mostrar(atual - 1));
form.addEventListener('submit', (e) => { e.preventDefault(); avancar(); });

/* ---------- Validação por etapa ---------- */

function validar(i) {
  const etapa = etapas[i];

  if (i === 1) {
    const marcados = etapa.querySelectorAll('input[name="servicos"]:checked').length;
    etapa.querySelector('input[name="servicos"]')
      .setCustomValidity(marcados ? '' : 'Marque pelo menos um tipo de serviço.');
  }
  if (i === 3) {
    const algum = ['telefone', 'whatsapp', 'email_contato', 'site']
      .some((nome) => form[nome].value.trim());
    form.telefone.setCustomValidity(algum ? '' : 'Preencha pelo menos um contato.');
  }
  if (i === 4) {
    form.senha2.setCustomValidity(
      form.senha.value === form.senha2.value ? '' : 'As senhas não coincidem.'
    );
  }

  for (const campo of etapa.querySelectorAll('input, select, textarea')) {
    if (!campo.reportValidity()) return false;
  }
  return true;
}

/* ---------- Máscaras ---------- */

function mascara(campo, formatar) {
  campo.addEventListener('input', () => {
    campo.value = formatar(campo.value.replace(/\D/g, ''));
  });
}

mascara(form.cnpj, (d) => d.slice(0, 14)
  .replace(/^(\d{2})(\d)/, '$1.$2')
  .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
  .replace(/\.(\d{3})(\d)/, '.$1/$2')
  .replace(/(\d{4})(\d)/, '$1-$2'));

mascara(form.cep, (d) => d.slice(0, 8).replace(/^(\d{5})(\d)/, '$1-$2'));

const telefone = (d) => d.slice(0, 11)
  .replace(/^(\d{2})(\d)/, '($1) $2')
  .replace(d.length > 10 ? /(\d{5})(\d)/ : /(\d{4})(\d)/, '$1-$2');
mascara(form.telefone, telefone);
mascara(form.whatsapp, telefone);

form.estado.addEventListener('input', () => {
  form.estado.value = form.estado.value.toUpperCase();
});

/* ---------- Revisão ---------- */

function montarRevisao() {
  const valor = (nome) => form[nome].value.trim() || '—';
  const servicos = [...form.querySelectorAll('input[name="servicos"]:checked')]
    .map((c) => c.value).join(', ');

  const linhas = [
    ['CNPJ', valor('cnpj')],
    ['Instituição', valor('nome')],
    ['Tipo', valor('tipo')],
    ['Descrição', valor('descricao')],
    ['Horário', valor('horario')],
    ['Serviços', servicos || '—'],
    ['Endereço', `${valor('logradouro')}, ${valor('numero')} - ${valor('bairro')}, ${valor('cidade')}/${valor('estado')} (${valor('cep')})`],
    ['Telefone', valor('telefone')],
    ['WhatsApp', valor('whatsapp')],
    ['E-mail', valor('email_contato')],
    ['Site', valor('site')],
    ['E-mail de acesso', valor('email')],
  ];

  const resumo = document.getElementById('resumo');
  resumo.replaceChildren();
  for (const [rotulo, texto] of linhas) {
    const dt = document.createElement('dt');
    const dd = document.createElement('dd');
    dt.textContent = rotulo;
    dd.textContent = texto;
    resumo.append(dt, dd);
  }
}

mostrar(0);