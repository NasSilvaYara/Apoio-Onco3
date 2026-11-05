// true  = não envia ao servidor e mostra a tela "Cadastro enviado!"
// false = envia o formulário por POST para a view do Django
const SO_FRONT = false;

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

/* ---------- Estado e cidade (select) ---------- */

const UFS = [
  ['AC', 'Acre'], ['AL', 'Alagoas'], ['AP', 'Amapá'], ['AM', 'Amazonas'],
  ['BA', 'Bahia'], ['CE', 'Ceará'], ['DF', 'Distrito Federal'],
  ['ES', 'Espírito Santo'], ['GO', 'Goiás'], ['MA', 'Maranhão'],
  ['MT', 'Mato Grosso'], ['MS', 'Mato Grosso do Sul'], ['MG', 'Minas Gerais'],
  ['PA', 'Pará'], ['PB', 'Paraíba'], ['PR', 'Paraná'], ['PE', 'Pernambuco'],
  ['PI', 'Piauí'], ['RJ', 'Rio de Janeiro'], ['RN', 'Rio Grande do Norte'],
  ['RS', 'Rio Grande do Sul'], ['RO', 'Rondônia'], ['RR', 'Roraima'],
  ['SC', 'Santa Catarina'], ['SP', 'São Paulo'], ['SE', 'Sergipe'],
  ['TO', 'Tocantins'],
];

const selEstado = form.estado;
const selCidade = form.cidade;
const cacheCidades = {};

const normalizar = (t) =>
  t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();

UFS.forEach(([sigla, nome]) => selEstado.append(new Option(nome, sigla)));

function definirCidade(nome) {
  const alvo = normalizar(nome);
  const opcao = [...selCidade.options].find((o) => normalizar(o.value) === alvo);
  if (opcao) selCidade.value = opcao.value;
}

async function carregarCidades(uf, cidadeSelecionada = '') {
  selCidade.disabled = true;

  if (!uf) {
    selCidade.replaceChildren(new Option('Selecione o estado primeiro', ''));
    return;
  }

  selCidade.replaceChildren(new Option('Carregando cidades...', ''));

  try {
    if (!cacheCidades[uf]) {
      const resp = await fetch(
        `https://servicodados.ibge.gov.br/api/v1/localidades/estados/${uf}/municipios?orderBy=nome`
      );
      if (!resp.ok) throw new Error('Falha ao buscar cidades');
      cacheCidades[uf] = (await resp.json()).map((m) => m.nome);
    }

    // se a pessoa trocou de estado enquanto carregava, ignora
    if (selEstado.value !== uf) return;

    selCidade.replaceChildren(new Option('Selecione a cidade', ''));
    cacheCidades[uf].forEach((nome) => selCidade.append(new Option(nome, nome)));
    selCidade.disabled = false;

    if (cidadeSelecionada) definirCidade(cidadeSelecionada);
  } catch (erro) {
    selCidade.replaceChildren(new Option('Erro ao carregar cidades', ''));
  }
}

selEstado.addEventListener('change', () => carregarCidades(selEstado.value));

// restaura os valores se o formulário voltar do servidor com erro
if (selEstado.dataset.valor) {
  selEstado.value = selEstado.dataset.valor;
  carregarCidades(selEstado.value, selCidade.dataset.valor);
}

/* ---------- Consulta de CNPJ ---------- */

document.addEventListener('DOMContentLoaded', () => {
  const campoCnpj = document.getElementById('cnpj');
  const razaoSocial = document.getElementById('razao_social');
  const nomeFantasia = document.getElementById('nome_fantasia');
  const resultado = document.getElementById('resultado-cnpj');

  campoCnpj.addEventListener('blur', async () => {
    const cnpj = campoCnpj.value.replace(/[^0-9A-Z]/gi, '').toUpperCase();

    razaoSocial.value = '';
    nomeFantasia.value = '';
    resultado.textContent = '';

    if (cnpj.length !== 14) {
      if (cnpj.length > 0) {
        resultado.textContent = 'Informe um CNPJ com 14 dígitos.';
      }
      return;
    }

    resultado.textContent = 'Consultando CNPJ...';

    try {
      const resposta = await fetch(`/api/cnpj/${cnpj}/`);
      const dados = await resposta.json();

      if (!resposta.ok || dados.valido !== true || dados.ativo !== true) {
        resultado.textContent =
          dados.mensagem || 'CNPJ inválido ou empresa inativa.';
        return;
      }

      razaoSocial.value = dados.razao_social || '';
      nomeFantasia.value = dados.nome_fantasia || '';

      const preencherSeVazio = (id, valor) => {
        const campo = document.getElementById(id);
        if (campo && !campo.value.trim() && valor) campo.value = valor;
      };
      preencherSeVazio('nome', dados.nome_fantasia || dados.razao_social);
      preencherSeVazio('cep', dados.cep);
      preencherSeVazio('endereco', dados.logradouro);
      preencherSeVazio('bairro', dados.bairro);
      preencherSeVazio('telefone', dados.telefone);
      preencherSeVazio('email_contato', dados.email);

      // estado e cidade agora são select
      if (dados.uf && !selEstado.value) {
        selEstado.value = dados.uf.toUpperCase();
        await carregarCidades(selEstado.value, dados.municipio);
      }

      resultado.textContent = 'CNPJ válido e empresa ativa.';
    } catch (erro) {
      resultado.textContent =
        'Não foi possível consultar o CNPJ. Tente novamente.';
    }
  });
});

/* ---------- Validação por etapa ---------- */

function validar(i) {
  const etapa = etapas[i];

  if (i === 1) {
    const marcados = etapa.querySelectorAll('input[name="servicos"]:checked').length;
    const primeiroServico = etapa.querySelector('input[name="servicos"]');
    if (primeiroServico) {
      primeiroServico.setCustomValidity(marcados ? '' : 'Marque pelo menos um tipo de serviço.');
    }
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

form.cnpj.addEventListener('input', () => {
  const cnpj = form.cnpj.value.replace(/[^0-9A-Z]/gi, '').toUpperCase().slice(0, 14);
  form.cnpj.value = cnpj
    .replace(/^([0-9A-Z]{2})([0-9A-Z])/, '$1.$2')
    .replace(/^([0-9A-Z]{2})\.([0-9A-Z]{3})([0-9A-Z])/, '$1.$2.$3')
    .replace(/^([0-9A-Z]{2})\.([0-9A-Z]{3})\.([0-9A-Z]{3})([0-9A-Z])/, '$1.$2.$3/$4')
    .replace(/([0-9A-Z]{4})([0-9]{1,2})$/, '$1-$2');
});

mascara(form.cep, (d) => d.slice(0, 8).replace(/^(\d{5})(\d)/, '$1-$2'));

const telefone = (d) => d.slice(0, 11)
  .replace(/^(\d{2})(\d)/, '($1) $2')
  .replace(d.length > 10 ? /(\d{5})(\d)/ : /(\d{4})(\d)/, '$1-$2');
mascara(form.telefone, telefone);
mascara(form.whatsapp, telefone);

/* ---------- Input de arquivo customizado ---------- */

const inputArquivo = document.getElementById('imagem_instituicao');
const textoArquivo = document.getElementById('nome-arquivo-selecionado');

if (inputArquivo && textoArquivo) {
  inputArquivo.addEventListener('change', function (e) {
    if (e.target.files.length > 0) {
      textoArquivo.textContent = e.target.files[0].name;
      textoArquivo.style.color = 'var(--roxo-escuro)';
      textoArquivo.style.fontWeight = '600';
    } else {
      textoArquivo.textContent = 'Escolher arquivo...';
    }
  });
}

/* ---------- Revisão ---------- */

function montarRevisao() {
  const valor = (nome) => form[nome].value.trim() || '—';
  const servicos = [...form.querySelectorAll('input[name="servicos"]:checked')]
    .map((c) => c.closest('label').textContent.trim()).join(', ');

  const inputImagem = form.querySelector('#imagem_instituicao');
  let nomeImagem = 'Nenhuma imagem selecionada';

  if (inputImagem && inputImagem.files && inputImagem.files.length > 0) {
    nomeImagem = inputImagem.files[0].name;
  }

  const linhas = [
    ['CNPJ', valor('cnpj')],
    ['Instituição', valor('nome')],
    ['Tipo', valor('tipo')],
    ['Descrição', valor('descricao')],
    ['Imagem/Logo', nomeImagem],
    ['Horário', valor('horario')],
    ['Serviços', servicos || '—'],
    ['Endereço', `${valor('endereco')}, ${valor('bairro')}, ${valor('cidade')}/${valor('estado')} (${valor('cep')})`],
    ['Número', valor('numero')],
    ['Complemento', valor('complemento')],
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