// Dashboard administrativo - ApoioOnco (somente front-end)
// Os dados abaixo são de exemplo: número de instituições por tipo de apoio em cada cidade.

const DADOS_DASHBOARD = JSON.parse(document.getElementById('dashboard-data').textContent);
const TIPOS = DADOS_DASHBOARD.tipos;
const DADOS = DADOS_DASHBOARD.cidades;

const cidades = Object.keys(DADOS).sort((a, b) => a.localeCompare(b, 'pt-BR'));

const campoBusca = document.getElementById('busca-topo');
const listaCidades = document.getElementById('lista-cidades');
const listaTipos = document.getElementById('tipos-apoio');
const textoFiltro = document.getElementById('chart-filtro');
const msgVazio = document.getElementById('chart-vazio');
const canvas = document.getElementById('grafico');

// Tira acentos e deixa minúsculo, para "sao paulo" achar "São Paulo"
const normalizar = (t) => t.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

// Sugestões de cidades cadastradas na caixa de busca
for (const cidade of cidades) {
  const opcao = document.createElement('option');
  opcao.value = cidade;
  listaCidades.append(opcao);
}

/* ---------- Dados conforme a busca ---------- */

function cidadesDaBusca() {
  const termo = normalizar(campoBusca.value.trim());
  if (!termo) return cidades;
  return cidades.filter((c) => normalizar(c).includes(termo));
}

function somar(lista) {
  return TIPOS.map((_, i) => lista.reduce((total, c) => total + DADOS[c][i], 0));
}

/* ---------- Gráfico ---------- */

let grafico = null;

if (window.Chart && canvas) {
  Chart.defaults.font.family = '"Plus Jakarta Sans", sans-serif';
  const coresDoGrafico = () => {
    const temaEscuro = document.documentElement.dataset.theme === 'dark';
    return {
      texto: temaEscuro ? '#ddd5e6' : '#3F3A3D',
      grade: temaEscuro ? '#49365d' : '#e2e8f0',
    };
  };
  const aplicarCoresDoGrafico = () => {
    const cores = coresDoGrafico();
    Chart.defaults.color = cores.texto;
    Chart.defaults.borderColor = cores.grade;
    if (grafico) {
      grafico.options.color = cores.texto;
      grafico.options.scales.x.ticks.color = cores.texto;
      grafico.options.scales.x.grid.color = cores.grade;
      grafico.options.scales.y.ticks.color = cores.texto;
      grafico.options.scales.y.grid.color = cores.grade;
      grafico.update();
    }
  };

  aplicarCoresDoGrafico();

  grafico = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: TIPOS,
      datasets: [{
        label: 'Instituições',
        data: somar(cidades),
        backgroundColor: '#7750A9',
        borderRadius: 8,
        maxBarThickness: 56,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: {
          beginAtZero: true,
          ticks: { precision: 0 },
          grid: { color: coresDoGrafico().grade },
        },
      },
    },
  });

  new MutationObserver(aplicarCoresDoGrafico).observe(
    document.documentElement,
    { attributes: true, attributeFilter: ['data-theme'] }
  );
} else if (canvas) {
  // Sem internet o Chart.js não carrega
  const aviso = document.createElement('p');
  aviso.textContent = 'Não foi possível carregar o gráfico.';
  canvas.replaceWith(aviso);
}

/* ---------- Atualização da tela ---------- */

function atualizar() {
  const encontradas = cidadesDaBusca();
  const totais = somar(encontradas);

  // Card "Quantidade por tipo de apoio"
  listaTipos.replaceChildren();
  TIPOS.forEach((tipo, i) => {
    const li = document.createElement('li');
    const nome = document.createElement('span');
    const total = document.createElement('strong');
    nome.textContent = tipo;
    total.textContent = totais[i];
    li.append(nome, total);
    listaTipos.append(li);
  });

  // Texto abaixo do título do gráfico
  if (!encontradas.length) {
    textoFiltro.textContent = '';
  } else if (encontradas.length === cidades.length) {
    textoFiltro.textContent = 'Todas as cidades cadastradas';
  } else if (encontradas.length <= 2) {
    textoFiltro.textContent = `Cidade: ${encontradas.join(' e ')}`;
  } else {
    textoFiltro.textContent = `${encontradas.length} cidades encontradas`;
  }

  // Gráfico e mensagem de "nada encontrado"
  msgVazio.hidden = encontradas.length > 0;
  if (grafico) {
    grafico.data.datasets[0].data = totais;
    grafico.canvas.style.visibility = encontradas.length ? 'visible' : 'hidden';
    grafico.update();
  }
}

campoBusca.addEventListener('input', () => {
  atualizar();
  if (!campoBusca.value.trim() && new URLSearchParams(window.location.search).get('cidade')) {
    document.getElementById('form-busca').submit();
  }
});

atualizar();