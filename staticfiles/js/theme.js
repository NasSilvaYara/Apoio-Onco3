(function () {
    var temaSalvo = localStorage.getItem('apoioonco-theme-v2');
    var temaInicial = temaSalvo === 'light' ? 'light' : 'dark';
    document.documentElement.dataset.theme = temaInicial;

    var botaoTema = document.querySelector('.theme-toggle-btn');
    if (!botaoTema) return;

    function atualizarBotao(tema) {
        var modoEscuroAtivo = tema === 'dark';
        botaoTema.setAttribute(
            'aria-label',
            modoEscuroAtivo ? 'Ativar tema claro' : 'Ativar tema escuro'
        );
        botaoTema.setAttribute('aria-pressed', String(modoEscuroAtivo));
    }

    atualizarBotao(temaInicial);
    botaoTema.addEventListener('click', function () {
        var novoTema = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
        document.documentElement.dataset.theme = novoTema;
        localStorage.setItem('apoioonco-theme-v2', novoTema);
        atualizarBotao(novoTema);
    });
})();
