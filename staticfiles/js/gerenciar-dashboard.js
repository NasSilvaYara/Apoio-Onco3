document.addEventListener('DOMContentLoaded', () => {
  const dataElement = document.getElementById('instituicoes-data');
  const list = document.getElementById('lista-instituicoes');
  const search = document.getElementById('busca-instituicoes');
  const typeFilter = document.getElementById('filtro-tipo');
  const stateFilter = document.getElementById('filtro-estado');
  const count = document.getElementById('contagem-instituicoes');
  const emptyState = document.getElementById('sem-resultado');
  const detailDialog = document.getElementById('painel-instituicao');
  const logoDialog = document.getElementById('visualizador-logo');
  const actionForm = document.getElementById('form-moderacao');
  const reasonContainer = document.querySelector('[data-rejection-reason]');
  const reasonInput = document.getElementById('motivo-reprovacao');
  const actionMessage = document.querySelector('[data-action-message]');
  const rows = [...list.querySelectorAll('[data-institution-id]')];
  const institutions = JSON.parse(dataElement.textContent);
  const byId = new Map(institutions.map((item) => [String(item.id), item]));
  const approvalConfirmation = document.getElementById('texto-confirmar-aprovacao').textContent.trim();
  const rejectionConfirmation = document.getElementById('texto-confirmar-reprovacao').textContent.trim();
  const inactivationConfirmation = document.getElementById('texto-confirmar-inativacao').textContent.trim();
  const actionError = document.getElementById('texto-erro-acao').textContent.trim();
  const noInformation = document.querySelector('[data-no-information]').textContent.trim();
  const resultCountTemplate = document.getElementById('texto-contagem').textContent.trim();
  const actionLabels = Object.fromEntries(
    [...document.querySelectorAll('[data-action-label]')].map((element) => [
      element.dataset.actionLabel,
      element.textContent.trim(),
    ])
  );
  let selectedStatus = 'pendente';
  let searchTimer;

  function statusCategory(status) {
    if (status === 'ativa') return 'ativo';
    if (status === 'pendente') return 'pendente';
    return 'desativado';
  }

  function normalize(value) {
    return String(value || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLocaleLowerCase();
  }

  function updateCounts() {
    const counts = {
      todas: rows.length,
      pendente: 0,
      ativo: 0,
      desativado: 0,
    };
    rows.forEach((row) => {
      counts[statusCategory(row.dataset.status)] += 1;
    });
    document.querySelectorAll('[data-status-count]').forEach((badge) => {
      badge.textContent = counts[badge.dataset.statusCount];
    });
  }

  function applyFilters() {
    const query = normalize(search.value.trim());
    const type = typeFilter.value;
    const state = stateFilter.value;
    let visible = 0;
    document.querySelectorAll('[data-status-filter]').forEach((button) => {
      const active = button.dataset.statusFilter === selectedStatus;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', String(active));
    });

    rows.forEach((row) => {
      const institution = byId.get(row.dataset.institutionId);
      const searchable = normalize([
        institution.nome,
        institution.cnpj,
        institution.cnpj_formatado,
        institution.cidade,
        institution.email_acesso,
        institution.email_contato,
      ].join(' '));
      const matches = (
        (selectedStatus === 'todas' || statusCategory(institution.status) === selectedStatus)
        && (!query || searchable.includes(query))
        && (!type || institution.tipo === type)
        && (!state || institution.estado === state)
      );
      row.hidden = !matches;
      if (matches) visible += 1;
    });

    count.textContent = resultCountTemplate.replace('{count}', visible);
    emptyState.hidden = visible !== 0;
  }

  function setText(element, value) {
    element.textContent = value === null || value === undefined || value === ''
      ? noInformation
      : value;
  }

  function safeLink(value) {
    if (!value) return '';
    try {
      const url = new URL(value, window.location.href);
      return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch {
      return '';
    }
  }

  function showInstitution(id) {
    const institution = byId.get(String(id));
    if (!institution) return;

    detailDialog.querySelectorAll('[data-detail]').forEach((element) => {
      const value = institution[element.dataset.detail];
      setText(element, Array.isArray(value) ? value.join(', ') : value);
    });

    const siteLink = detailDialog.querySelector('[data-detail-link="site"]');
    const siteUrl = safeLink(institution.site);
    if (siteUrl) {
      siteLink.href = siteUrl;
      siteLink.textContent = institution.site;
      siteLink.hidden = false;
    } else {
      siteLink.removeAttribute('href');
      siteLink.textContent = noInformation;
      siteLink.hidden = false;
    }

    const logoContainer = detailDialog.querySelector('[data-logo-container]');
    const logo = detailDialog.querySelector('[data-logo]');
    const logoEmpty = detailDialog.querySelector('[data-logo-empty]');
    const enlargeLogoButton = detailDialog.querySelector('[data-enlarge-logo]');
    const logoUrl = safeLink(institution.logo_url);
    logoContainer.hidden = false;
    logo.hidden = !logoUrl;
    logoEmpty.hidden = Boolean(logoUrl);
    enlargeLogoButton.hidden = !logoUrl;
    if (logoUrl) logo.src = logoUrl;
    else logo.removeAttribute('src');

    actionForm.elements.instituicao_id.value = institution.id;
    actionForm.dataset.institutionName = institution.nome;
    actionMessage.textContent = '';
    reasonInput.value = '';
    reasonContainer.hidden = true;
    actionForm.querySelector('[data-show-rejection]').hidden = institution.status !== 'pendente';
    actionForm.querySelector('[data-confirm-rejection]').hidden = true;
    actionForm.querySelector('[data-cancel-rejection]').hidden = true;
    actionForm.querySelector('[data-action-inactivate]').hidden = institution.status !== 'ativa';
    actionForm.querySelector('[data-action-reactivate]').hidden =
      !['inativa', 'rejeitada'].includes(institution.status);
    actionForm.querySelector('[name="acao"][value="aprovar"]').hidden =
      institution.status !== 'pendente';
    detailDialog.showModal();
  }

  function criarAcaoIcone(acao, classe, icone) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `acao-icone ${classe}`;
    button.dataset.quickAction = acao;
    button.setAttribute('aria-label', actionLabels[acao]);
    button.title = actionLabels[acao];
    const icon = document.createElement('i');
    icon.className = `ti ${icone}`;
    icon.setAttribute('aria-hidden', 'true');
    button.append(icon);
    return button;
  }

  function atualizarAcoesDaLinha(row, status) {
    const actions = row.querySelector('[data-action-cell]');
    const buttons = [];
    if (status === 'pendente') {
      buttons.push(
        criarAcaoIcone('rejeitar', 'acao-icone--negativa', 'ti-ban'),
        criarAcaoIcone('aprovar', 'acao-icone--positiva', 'ti-check')
      );
    } else if (status === 'ativa') {
      buttons.push(
        criarAcaoIcone('inativar', 'acao-icone--negativa', 'ti-ban')
      );
    } else {
      buttons.push(
        criarAcaoIcone('reativar', 'acao-icone--positiva', 'ti-check')
      );
    }
    actions.replaceChildren(...buttons);
  }

  function updateInstitutionStatus(id, responseData) {
    const institution = byId.get(String(id));
    const row = rows.find((item) => item.dataset.institutionId === String(id));
    institution.status = responseData.status;
    institution.status_display = responseData.status_display;
    institution.avaliado_em = responseData.avaliado_em;
    institution.atualizado_em = responseData.atualizado_em;
    institution.motivo_rejeicao = responseData.motivo_rejeicao;
    row.dataset.status = responseData.status;
    row.querySelector('[data-status-label]').textContent = responseData.status_display;
    atualizarAcoesDaLinha(row, responseData.status);
    updateCounts();
    applyFilters();
  }

  document.querySelectorAll('[data-status-filter]').forEach((button) => {
    button.addEventListener('click', () => {
      selectedStatus = button.dataset.statusFilter;
      document.querySelectorAll('[data-status-filter]').forEach((item) => {
        const active = item === button;
        item.classList.toggle('is-active', active);
        item.setAttribute('aria-pressed', String(active));
      });
      applyFilters();
    });
  });

  search.addEventListener('input', () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(applyFilters, 180);
  });
  typeFilter.addEventListener('change', applyFilters);
  stateFilter.addEventListener('change', applyFilters);

  list.addEventListener('click', (event) => {
    const row = event.target.closest('[data-institution-id]');
    if (!row) return;

    const action = event.target.closest('[data-quick-action]');
    if (action) {
      showInstitution(row.dataset.institutionId);
      if (action.dataset.quickAction === 'rejeitar') {
        actionForm.querySelector('[data-show-rejection]').click();
      } else {
        actionForm.requestSubmit(
          actionForm.querySelector(`[name="acao"][value="${action.dataset.quickAction}"]`)
        );
      }
      return;
    }

    if (event.target.closest('[data-open-institution]')) {
      showInstitution(row.dataset.institutionId);
      return;
    }

    if (!event.target.closest('button, a, input, select, textarea, [contenteditable="true"]')) {
      showInstitution(row.dataset.institutionId);
    }
  });

  detailDialog.addEventListener('click', (event) => {
    if (event.target === detailDialog || event.target.closest('[data-close-panel]')) {
      detailDialog.close();
    }
  });

  actionForm.querySelector('[data-show-rejection]').addEventListener('click', () => {
    reasonContainer.hidden = false;
    actionForm.querySelector('[data-show-rejection]').hidden = true;
    actionForm.querySelector('[data-confirm-rejection]').hidden = false;
    actionForm.querySelector('[data-cancel-rejection]').hidden = false;
    reasonInput.focus();
  });

  actionForm.querySelector('[data-cancel-rejection]').addEventListener('click', () => {
    reasonContainer.hidden = true;
    reasonInput.value = '';
    actionForm.querySelector('[data-show-rejection]').hidden = false;
    actionForm.querySelector('[data-confirm-rejection]').hidden = true;
    actionForm.querySelector('[data-cancel-rejection]').hidden = true;
  });

  actionForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const action = event.submitter.value;
    const confirmation = action === 'aprovar'
      ? approvalConfirmation
      : action === 'rejeitar'
        ? rejectionConfirmation
        : action === 'inativar'
          ? inactivationConfirmation
        : '';
    if (confirmation && !window.confirm(confirmation)) return;

    actionMessage.textContent = '';
    const formData = new FormData(actionForm);
    formData.set('acao', action);
    try {
      const response = await fetch(actionForm.action || window.location.href, {
        method: 'POST',
        body: formData,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin',
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || actionError);
      updateInstitutionStatus(actionForm.elements.instituicao_id.value, result);
      detailDialog.close();
      document.querySelector(`[data-status-filter="${selectedStatus}"]`).focus();
    } catch {
      actionMessage.textContent = actionError;
    }
  });

  detailDialog.addEventListener('click', (event) => {
    if (event.target.closest('[data-enlarge-logo]')) {
      const logo = detailDialog.querySelector('[data-logo]');
      const enlarged = logoDialog.querySelector('[data-enlarged-logo]');
      enlarged.src = logo.src;
      enlarged.alt = logo.alt;
      logoDialog.showModal();
    }
  });

  logoDialog.addEventListener('click', (event) => {
    if (event.target === logoDialog || event.target.closest('[data-close-logo]')) {
      logoDialog.close();
    }
  });

  updateCounts();
  applyFilters();
});
