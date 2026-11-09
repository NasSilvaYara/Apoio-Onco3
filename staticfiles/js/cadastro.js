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

async function avancar() {
  if (btnAvancar.disabled) return;
  btnAvancar.disabled = true;
  try {
    if (!await validar(atual)) return;
    if (atual < etapas.length - 1) {
      mostrar(atual + 1);
    } else {
      form.submit();
    }
  } finally {
    btnAvancar.disabled = false;
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

let cnpjConsulta = { valor: '', promessa: null };
const retryAfterInicial = Number(form.dataset.cnpjRetryAfter);
let cnpjRetryAt = Number.isInteger(retryAfterInicial) && retryAfterInicial >= 0
  ? Date.now() + retryAfterInicial * 1000
  : 0;

function cnpjValido(valor) {
  const cnpj = valor.replace(/[^0-9A-Z]/gi, '').toUpperCase();
  if (!/^[0-9A-Z]{12}[0-9]{2}$/.test(cnpj) || new Set(cnpj).size === 1) {
    return false;
  }

  const pesosDv1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const calcularDigito = (base, pesos) => {
    const soma = [...base].reduce(
      (total, caractere, indice) =>
        total + (caractere.charCodeAt(0) - 48) * pesos[indice],
      0
    );
    const resto = soma % 11;
    return resto < 2 ? '0' : String(11 - resto);
  };

  const digito1 = calcularDigito(cnpj.slice(0, 12), pesosDv1);
  const digito2 = calcularDigito(
    cnpj.slice(0, 12) + digito1,
    [6, ...pesosDv1]
  );
  return cnpj.slice(12) === digito1 + digito2;
}

async function consultarCnpj(cnpj) {
  if (cnpjConsulta.valor === cnpj && cnpjConsulta.promessa) {
    return cnpjConsulta.promessa;
  }

  const campoCnpj = form.cnpj;
  const resultado = document.getElementById('resultado-cnpj');
  const razaoSocial = document.getElementById('razao_social');
  const nomeFantasia = document.getElementById('nome_fantasia');
  const tokenValidacao = document.getElementById('token_validacao_cnpj');
  if (Date.now() < cnpjRetryAt) {
    const segundos = Math.ceil((cnpjRetryAt - Date.now()) / 1000);
    resultado.textContent =
      `A consulta do CNPJ atingiu o limite de requisições. Tente novamente em ${segundos} segundos.`;
    resultado.classList.add('erro-campo');
    return false;
  }
  const promessa = (async () => {
      resultado.textContent = 'Consultando CNPJ...';
      resultado.classList.remove('erro-campo');
      tokenValidacao.value = '';

      try {
        const resposta = await fetch(`/api/cnpj/${cnpj}/`);
        const dados = await resposta.json();
        if (resposta.status === 429) {
          const retryAfter = Number(resposta.headers.get('Retry-After'));
          if (Number.isInteger(retryAfter) && retryAfter >= 0) {
            cnpjRetryAt = Date.now() + retryAfter * 1000;
          }
        }

        if (campoCnpj.value.replace(/[^0-9A-Z]/gi, '').toUpperCase() !== cnpj) {
          return false;
        }

        if (!resposta.ok || dados.valido !== true || dados.ativo !== true) {
          resultado.textContent =
            dados.mensagem || 'CNPJ inválido ou empresa inativa.';
          resultado.classList.add('erro-campo');
          return false;
        }

        tokenValidacao.value = dados.token_validacao || '';
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

        if (dados.uf && !selEstado.value) {
          selEstado.value = dados.uf.toUpperCase();
          await carregarCidades(selEstado.value, dados.municipio);
        }

        resultado.textContent = 'CNPJ válido e empresa ativa.';
        resultado.classList.remove('erro-campo');
        return true;
      } catch (erro) {
        if (campoCnpj.value.replace(/[^0-9A-Z]/gi, '').toUpperCase() === cnpj) {
          resultado.textContent =
            'Não foi possível consultar o CNPJ no momento. Tente novamente mais tarde.';
          resultado.classList.add('erro-campo');
        }
        return false;
      }
    })();
  cnpjConsulta = { valor: cnpj, promessa };
  const valido = await promessa;
  if (!valido && cnpjConsulta.promessa === promessa) {
    cnpjConsulta = { valor: '', promessa: null };
  }
  return valido;
}

form.cnpj.addEventListener('blur', async () => {
  const cnpj = form.cnpj.value.replace(/[^0-9A-Z]/gi, '').toUpperCase();
  document.getElementById('razao_social').value = '';
  document.getElementById('nome_fantasia').value = '';
  document.getElementById('resultado-cnpj').textContent = '';
  document.getElementById('resultado-cnpj').classList.remove('erro-campo');

  if (cnpj.length !== 14) {
    if (cnpj.length > 0) {
      document.getElementById('resultado-cnpj').textContent =
        'CNPJ inválido. Verifique os números informados.';
      document.getElementById('resultado-cnpj').classList.add('erro-campo');
    }
    return;
  }

  if (!cnpjValido(cnpj)) {
    document.getElementById('resultado-cnpj').textContent =
      'CNPJ inválido. Verifique os números informados.';
    document.getElementById('resultado-cnpj').classList.add('erro-campo');
    return;
  }

  await consultarCnpj(cnpj);
});

/* ---------- Validação por etapa ---------- */

async function validar(i) {
  const etapa = etapas[i];

  if (i === 0) {
    const valido = cnpjValido(form.cnpj.value);
    const mensagemCnpjInvalido =
      'CNPJ inválido. Verifique os números informados.';
    form.cnpj.setCustomValidity(
      valido ? '' : mensagemCnpjInvalido
    );
    if (!valido) {
      document.getElementById('resultado-cnpj').textContent =
        mensagemCnpjInvalido;
      document.getElementById('resultado-cnpj').classList.add('erro-campo');
    }
    if (!valido) {
      form.cnpj.reportValidity();
      return false;
    }
    form.cnpj.setCustomValidity('');
    if (!await consultarCnpj(form.cnpj.value.replace(/[^0-9A-Z]/gi, '').toUpperCase())) {
      form.cnpj.setCustomValidity(
        document.getElementById('resultado-cnpj').textContent
      );
      form.cnpj.reportValidity();
      return false;
    }
  }

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
  form.cnpj.setCustomValidity('');
  form.cnpj.removeAttribute('aria-invalid');
  document.getElementById('resultado-cnpj').textContent = '';
  document.getElementById('resultado-cnpj').classList.remove('erro-campo');
  document.getElementById('token_validacao_cnpj').value = '';
  cnpjConsulta = { valor: '', promessa: null };
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

function exibirErrosServidor() {
  const erros = document.querySelectorAll('#erros-servidor [data-field]');
  if (!erros.length) return;

  let primeiraEtapa = etapas.length - 1;
  let primeiroCampo = null;

  for (const erro of erros) {
    const nomeCampo = erro.dataset.field;
    const campo = [...form.elements].find((elemento) => elemento.name === nomeCampo);
    const etapa = campo ? campo.closest('.etapa') : etapas[etapas.length - 1];
    const indiceEtapa = etapas.indexOf(etapa);
    primeiraEtapa = Math.min(primeiraEtapa, indiceEtapa);

    const mensagem = document.createElement('p');
    mensagem.className = 'erro-campo';
    mensagem.setAttribute('role', 'alert');
    mensagem.textContent = erro.textContent.trim();

    const destino = campo
      ? campo.closest('.formulario-login, .servicos') || campo.parentElement
      : etapa;
    destino.append(mensagem);

    if (campo) {
      campo.setAttribute('aria-invalid', 'true');
      campo.addEventListener('input', () => {
        campo.removeAttribute('aria-invalid');
        mensagem.remove();
      }, { once: true });
      campo.addEventListener('change', () => {
        campo.removeAttribute('aria-invalid');
        mensagem.remove();
      }, { once: true });
      if (!primeiroCampo || indiceEtapa < etapas.indexOf(primeiroCampo.closest('.etapa'))) {
        primeiroCampo = campo;
      }
    }
  }

  document.getElementById('erros-servidor').remove();
  mostrar(primeiraEtapa);
  if (primeiroCampo) primeiroCampo.focus();
}

if (form.dataset.cadastroEnviado === 'true') {
  tituloBanner.textContent = 'Obrigada por fazer parte!';
} else {
  mostrar(0);
  exibirErrosServidor();
}