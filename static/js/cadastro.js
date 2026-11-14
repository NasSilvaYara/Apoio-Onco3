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

async function mostrarErroCadastro(mensagem, titulo = 'Verifique os dados informados') {
  const mensagemAlternativa = document.getElementById('erro-cadastro-modal');
  if (!window.Swal) {
    if (mensagemAlternativa) {
      mensagemAlternativa.textContent = mensagem;
      mensagemAlternativa.hidden = false;
    }
    console.error('SweetAlert2 não foi carregado; erro de cadastro:', mensagem);
    return;
  }

  if (mensagemAlternativa) {
    mensagemAlternativa.textContent = '';
    mensagemAlternativa.hidden = true;
  }

  document.activeElement?.blur();
  await window.Swal.fire({
    icon: 'error',
    title: titulo,
    text: mensagem,
    returnFocus: false,
    confirmButtonText: 'Entendi',
    buttonsStyling: false,
    customClass: {
      popup: 'cadastro-swal-popup',
      title: 'cadastro-swal-title',
      htmlContainer: 'cadastro-swal-message',
      confirmButton: 'cadastro-swal-confirm',
    },
  });
}

function mensagemCampoInvalido(campo) {
  const rotulo = form.querySelector(`label[for="${campo.id}"]`)?.textContent.trim();
  if (campo.validity.valueMissing) return `Preencha o campo ${rotulo || campo.name}.`;
  if (campo.type === 'email' && campo.validity.typeMismatch) {
    return 'Informe um endereço de e-mail válido.';
  }
  if (campo.validity.tooShort) {
    return `Use ao menos ${campo.minLength} caracteres no campo ${rotulo || campo.name}.`;
  }
  return campo.validationMessage;
}

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
  if (document.activeElement?.closest('.etapa')
    && document.activeElement.closest('.etapa') !== etapas[i]) {
    document.activeElement.blur();
  }
  etapas.forEach((etapa, indice) => {
    etapa.inert = indice !== i;
    etapa.setAttribute('aria-hidden', indice !== i ? 'true' : 'false');
  });
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
    if (selEstado.value !== uf) return;
    selCidade.replaceChildren(new Option('Erro ao carregar cidades', ''));
    await mostrarErroCadastro(
      'Não foi possível carregar as cidades deste estado. Verifique sua conexão e tente novamente.',
      'Falha ao carregar cidades'
    );
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
let cnpjAvisoApiExibido = false;
let ultimoCnpjLimpo = '';
const retryAfterInicial = form.dataset.cnpjRetryAfter
  ? Number(form.dataset.cnpjRetryAfter)
  : 0;
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
    const consultaAnterior = await cnpjConsulta.promessa;
    if (!consultaAnterior.retryable || Date.now() < cnpjRetryAt) {
      return consultaAnterior;
    }
    cnpjConsulta = { valor: '', promessa: null };
  }

  const campoCnpj = form.cnpj;
  const resultado = document.getElementById('resultado-cnpj');
  const razaoSocial = document.getElementById('razao_social');
  const nomeFantasia = document.getElementById('nome_fantasia');
  const tokenValidacao = document.getElementById('token_validacao_cnpj');
  if (Date.now() < cnpjRetryAt) {
    const segundos = Math.ceil((cnpjRetryAt - Date.now()) / 1000);
    const mensagem =
      `A consulta do CNPJ atingiu o limite de requisições. Tente novamente em ${segundos} segundos.`;
    resultado.textContent = mensagem;
    resultado.classList.add('erro-campo');
    const consultaLimitada = (async () => {
      await mostrarErroCadastro(mensagem, 'Consulta temporariamente indisponível');
      return {
        valido: false,
        alertaExibido: true,
        retryable: true,
      };
    })();
    cnpjConsulta = { valor: cnpj, promessa: consultaLimitada };
    return consultaLimitada;
  }
  const promessa = (async () => {
      resultado.textContent = 'Consultando CNPJ...';
      resultado.classList.remove('erro-campo');
      tokenValidacao.value = '';

      try {
        const resposta = await fetch(`/api/cnpj/${cnpj}/`);
        let dados = {};
        try {
          dados = await resposta.json();
        } catch (erro) {
          if (resposta.ok) throw erro;
        }
        if (resposta.status === 429) {
          const retryAfterHeader = resposta.headers.get('Retry-After');
          const retryAfter = retryAfterHeader && /^\d+$/.test(retryAfterHeader)
            ? Number(retryAfterHeader)
            : 60;
          cnpjRetryAt = Date.now() + retryAfter * 1000;
        }

        if (campoCnpj.value.replace(/[^0-9A-Z]/gi, '').toUpperCase() !== cnpj) {
          return { valido: false, alertaExibido: false };
        }

        if (resposta.status === 429 || !resposta.ok && resposta.status >= 500) {
          const mensagem = resposta.status === 429
            ? dados.mensagem || 'A consulta atingiu o limite de requisições. Aguarde um momento e tente novamente.'
            : 'O serviço de consulta está temporariamente indisponível. Tente novamente mais tarde.';
          resultado.textContent = mensagem;
          resultado.classList.add('erro-campo');
          await mostrarErroCadastro(mensagem, 'Consulta temporariamente indisponível');
          cnpjAvisoApiExibido = true;
          if (resposta.status >= 500) cnpjRetryAt = Date.now() + 30_000;
          return {
            valido: false,
            alertaExibido: true,
            retryable: resposta.status === 429 || resposta.status >= 500,
          };
        }

        if (!resposta.ok || dados.valido !== true || dados.ativo !== true) {
          resultado.textContent =
            dados.mensagem || 'Não foi possível validar este CNPJ. Confira os dados informados.';
          resultado.classList.add('erro-campo');
          return { valido: false, alertaExibido: false };
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
        return { valido: true, alertaExibido: false };
      } catch (erro) {
        if (campoCnpj.value.replace(/[^0-9A-Z]/gi, '').toUpperCase() === cnpj) {
          const mensagem =
            'Não foi possível consultar o CNPJ no momento. Verifique sua conexão e tente novamente mais tarde.';
          resultado.textContent = mensagem;
          resultado.classList.add('erro-campo');
          await mostrarErroCadastro(mensagem, 'Falha na consulta do CNPJ');
          cnpjAvisoApiExibido = true;
          cnpjRetryAt = Date.now() + 30_000;
        }
        return {
          valido: false,
          alertaExibido: cnpjAvisoApiExibido,
          retryable: true,
        };
      }
    })();
  cnpjConsulta = { valor: cnpj, promessa };
  return promessa;
}

form.cnpj.addEventListener('blur', async () => {
  const cnpj = form.cnpj.value.replace(/\D/g, '');
  if (cnpjConsulta.valor === cnpj && cnpjConsulta.promessa) {
    const consultaAnterior = await cnpjConsulta.promessa;
    if (!consultaAnterior.retryable || Date.now() < cnpjRetryAt) return;
    cnpjConsulta = { valor: '', promessa: null };
  }

  document.getElementById('razao_social').value = '';
  document.getElementById('nome_fantasia').value = '';
  document.getElementById('resultado-cnpj').textContent = '';
  document.getElementById('resultado-cnpj').classList.remove('erro-campo');

  if (!/^\d{14}$/.test(cnpj)) {
    if (cnpj.length > 0) {
      document.getElementById('resultado-cnpj').textContent =
        'Informe um CNPJ com exatamente 14 dígitos numéricos.';
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

  cnpjAvisoApiExibido = false;
  await consultarCnpj(cnpj);
});

/* ---------- Validação por etapa ---------- */

async function validar(i) {
  const etapa = etapas[i];

  if (i === 0) {
    const cnpjLimpo = form.cnpj.value.replace(/\D/g, '');
    const formatoValido = /^\d{14}$/.test(cnpjLimpo);
    const valido = formatoValido && cnpjValido(cnpjLimpo);
    const mensagemCnpjInvalido =
      formatoValido
        ? 'CNPJ inválido. Verifique os números informados.'
        : 'Informe um CNPJ com exatamente 14 dígitos numéricos.';
    form.cnpj.setCustomValidity(
      valido ? '' : mensagemCnpjInvalido
    );
    if (!valido) {
      document.getElementById('resultado-cnpj').textContent =
        mensagemCnpjInvalido;
      document.getElementById('resultado-cnpj').classList.add('erro-campo');
    }
    if (!valido) {
      form.cnpj.setAttribute('aria-invalid', 'true');
      await mostrarErroCadastro(mensagemCnpjInvalido);
      form.cnpj.focus();
      return false;
    }
    form.cnpj.setCustomValidity('');
    cnpjAvisoApiExibido = false;
    if (cnpjConsulta.valor !== cnpjLimpo || !cnpjConsulta.promessa) {
      const mensagem = 'Saia do campo CNPJ para consultar os dados antes de continuar.';
      document.getElementById('resultado-cnpj').textContent = mensagem;
      document.getElementById('resultado-cnpj').classList.add('erro-campo');
      await mostrarErroCadastro(mensagem, 'Valide o CNPJ');
      form.cnpj.focus();
      return false;
    }
    const consulta = await cnpjConsulta.promessa;
    if (!consulta.valido) {
      form.cnpj.setCustomValidity(
        document.getElementById('resultado-cnpj').textContent
      );
      form.cnpj.setAttribute('aria-invalid', 'true');
      if (!consulta.alertaExibido) {
        await mostrarErroCadastro(form.cnpj.validationMessage);
      }
      form.cnpj.focus();
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
    if (!campo.checkValidity()) {
      await mostrarErroCadastro(mensagemCampoInvalido(campo));
      campo.focus();
      return false;
    }
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
  const cnpjNovo = form.cnpj.value.replace(/\D/g, '').slice(0, 14);
  form.cnpj.setCustomValidity('');
  form.cnpj.removeAttribute('aria-invalid');
  if (cnpjNovo !== ultimoCnpjLimpo) {
    cnpjConsulta = { valor: '', promessa: null };
    cnpjAvisoApiExibido = false;
    document.getElementById('resultado-cnpj').textContent = '';
    document.getElementById('resultado-cnpj').classList.remove('erro-campo');
    document.getElementById('token_validacao_cnpj').value = '';
  }
  ultimoCnpjLimpo = cnpjNovo;
  const cnpj = form.cnpj.value.replace(/\D/g, '').slice(0, 14);
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

async function exibirErrosServidor() {
  const erros = document.querySelectorAll('#erros-servidor [data-field]');
  if (!erros.length) return;

  const mensagensServidor = [...erros]
    .map((erro) => erro.textContent.trim())
    .filter(Boolean);
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
  await mostrarErroCadastro(
    mensagensServidor.join('\n'),
    'Não foi possível concluir o cadastro'
  );
  if (primeiroCampo) primeiroCampo.focus();
}

if (form.dataset.cadastroEnviado === 'true') {
  tituloBanner.textContent = 'Obrigada por fazer parte!';
} else {
  mostrar(0);
  exibirErrosServidor();
}