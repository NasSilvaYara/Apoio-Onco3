
const TODOS_APOIOS = [
  'Banco de perucas',
  'Banco de lenços',
  'Apoio psicológico',
  'Assistência social',
];

/* ---------- Trocar logo (prévia) ---------- */

const arquivoLogo = document.getElementById('logo-arquivo');
const previewLogo = document.getElementById('logo-preview');

document.getElementById('btn-trocar-logo')
  .addEventListener('click', () => arquivoLogo.click());

arquivoLogo.addEventListener('change', () => {
  const arquivo = arquivoLogo.files[0];
  if (!arquivo) return;
  const img = document.createElement('img');
  img.src = URL.createObjectURL(arquivo);
  img.alt = 'Prévia da nova logo';
  previewLogo.replaceChildren(img);
});

/* ---------- Tipos de apoio (chips) ---------- */

const chips = document.getElementById('chips');
const btnAdd = document.getElementById('btn-add-apoio');
const menu = document.getElementById('menu-apoios');

const selecionados = () =>
  [...chips.querySelectorAll('input[name="servicos"]')].map((i) => i.value);

function criarChip(valor) {
  const chip = document.createElement('span');
  chip.className = 'chip';
  chip.append(valor);

  const remover = document.createElement('button');
  remover.type = 'button';
  remover.className = 'chip-remover';
  remover.setAttribute('aria-label', `Remover ${valor}`);
  remover.innerHTML = '<i class="ti ti-x" aria-hidden="true"></i>';

  const campo = document.createElement('input');
  campo.type = 'hidden';
  campo.name = 'servicos';
  campo.value = valor;

  chip.append(remover, campo);
  chips.append(chip);
}

chips.addEventListener('click', (e) => {
  const botao = e.target.closest('.chip-remover');
  if (botao) botao.closest('.chip').remove();
});

function montarMenu() {
  const faltando = TODOS_APOIOS.filter((a) => !selecionados().includes(a));
  menu.replaceChildren();

  if (!faltando.length) {
    const vazio = document.createElement('li');
    vazio.className = 'vazio';
    vazio.textContent = 'Todos os apoios já foram adicionados.';
    menu.append(vazio);
    return;
  }

  for (const apoio of faltando) {
    const li = document.createElement('li');
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.textContent = apoio;
    botao.addEventListener('click', () => {
      criarChip(apoio);
      fecharMenu();
    });
    li.append(botao);
    menu.append(li);
  }
}

function fecharMenu() {
  menu.hidden = true;
  btnAdd.setAttribute('aria-expanded', 'false');
}

btnAdd.addEventListener('click', () => {
  if (menu.hidden) {
    montarMenu();
    menu.hidden = false;
    btnAdd.setAttribute('aria-expanded', 'true');
  } else {
    fecharMenu();
  }
});

document.addEventListener('click', (e) => {
  if (!e.target.closest('.adicionar-apoio')) fecharMenu();
});

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') fecharMenu();
});