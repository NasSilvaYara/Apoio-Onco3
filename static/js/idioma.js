document.querySelectorAll("[data-language-selector]").forEach(function (seletor) {
  var gatilho = seletor.querySelector(".seletor-idioma__gatilho");
  var lista = seletor.querySelector(".seletor-idioma__lista");
  var opcoes = Array.from(seletor.querySelectorAll('[role="menuitem"]'));

  if (!gatilho || !lista || !opcoes.length) return;

  function fechar(devolverFoco) {
    gatilho.setAttribute("aria-expanded", "false");
    lista.hidden = true;
    if (devolverFoco) gatilho.focus();
  }

  function abrir(indiceInicial) {
    gatilho.setAttribute("aria-expanded", "true");
    lista.hidden = false;
    if (indiceInicial !== undefined) opcoes[indiceInicial].focus();
  }

  gatilho.addEventListener("click", function () {
    if (gatilho.getAttribute("aria-expanded") === "true") {
      fechar(false);
    } else {
      abrir();
    }
  });

  seletor.addEventListener("keydown", function (event) {
    var indice = opcoes.indexOf(document.activeElement);

    if (event.key === "Escape" && !lista.hidden) {
      event.preventDefault();
      fechar(true);
      return;
    }

    if (document.activeElement === gatilho && event.key === "ArrowDown") {
      event.preventDefault();
      abrir(0);
      return;
    }

    if (document.activeElement === gatilho && event.key === "ArrowUp") {
      event.preventDefault();
      abrir(opcoes.length - 1);
      return;
    }

    if (lista.hidden || indice === -1) return;

    var proximoIndice;
    if (event.key === "ArrowDown") {
      proximoIndice = (indice + 1) % opcoes.length;
    } else if (event.key === "ArrowUp") {
      proximoIndice = (indice - 1 + opcoes.length) % opcoes.length;
    } else if (event.key === "Home") {
      proximoIndice = 0;
    } else if (event.key === "End") {
      proximoIndice = opcoes.length - 1;
    }

    if (proximoIndice !== undefined) {
      event.preventDefault();
      opcoes[proximoIndice].focus();
    }
  });

  document.addEventListener("click", function (event) {
    if (!seletor.contains(event.target) && !lista.hidden) fechar(false);
  });

  seletor.addEventListener("focusout", function (event) {
    if (!seletor.contains(event.relatedTarget) && !lista.hidden) fechar(false);
  });
});
