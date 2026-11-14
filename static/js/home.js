/* ---------- Aviso de acesso exclusivo para instituições ---------- */
const stateSelect = document.querySelector('#filtro-estado');
const stateTrigger = document.querySelector('.state-filter__trigger');
const stateOptions = document.querySelector('.state-filter__options');

if (stateSelect && stateTrigger && stateOptions) {
    const stateLabel = stateTrigger.querySelector('.state-filter__label');
    const stateOptionButtons = Array.from(
        stateOptions.querySelectorAll('[data-state-value]')
    );

    function closeStateOptions(restoreFocus = false) {
        stateOptions.hidden = true;
        stateTrigger.setAttribute('aria-expanded', 'false');
        if (restoreFocus) stateTrigger.focus();
    }

    function openStateOptions() {
        stateOptions.hidden = false;
        stateTrigger.setAttribute('aria-expanded', 'true');
        const selected = stateOptions.querySelector('[aria-selected="true"]');
        (selected || stateOptionButtons[0])?.focus();
    }

    function selectState(option) {
        const value = option.dataset.stateValue;
        stateSelect.value = value;
        stateLabel.textContent = option.textContent.trim();
        stateOptionButtons.forEach((button) => {
            button.setAttribute(
                'aria-selected',
                String(button === option)
            );
        });
        closeStateOptions(true);
    }

    stateSelect.hidden = true;
    stateTrigger.hidden = false;

    stateTrigger.addEventListener('click', () => {
        if (stateOptions.hidden) openStateOptions();
        else closeStateOptions();
    });

    stateOptionButtons.forEach((option, index) => {
        option.addEventListener('click', () => selectState(option));
        option.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                event.preventDefault();
                closeStateOptions(true);
            } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                const direction = event.key === 'ArrowDown' ? 1 : -1;
                const nextIndex = (index + direction + stateOptionButtons.length)
                    % stateOptionButtons.length;
                stateOptionButtons[nextIndex].focus();
            } else if (event.key === 'Home') {
                event.preventDefault();
                stateOptionButtons[0].focus();
            } else if (event.key === 'End') {
                event.preventDefault();
                stateOptionButtons[stateOptionButtons.length - 1].focus();
            }
        });
    });

    stateTrigger.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            openStateOptions();
        }
    });

    document.addEventListener('click', (event) => {
        if (!event.target.closest('.state-filter')) closeStateOptions();
    });
}

const loginGate = document.querySelector('#login-gate');
const loginGateOpeners = document.querySelectorAll('[data-login-gate-open]');
const loginGateCloseButton = document.querySelector('[data-login-gate-close]');

if (loginGate && loginGateCloseButton) {
    loginGateOpeners.forEach((opener) => {
        opener.addEventListener('click', (event) => {
            event.preventDefault();
            loginGate.showModal();
        });
    });

    loginGateCloseButton.addEventListener('click', () => {
        loginGate.close();
    });

    loginGate.addEventListener('click', (event) => {
        if (event.target === loginGate) {
            loginGate.close();
        }
    });
}

const menuToggle = document.querySelector('.menu-toggle');
const navLinks = document.querySelector('#menu-principal');

if (menuToggle && navLinks) {
    function setMenuOpen(isOpen) {
        menuToggle.classList.toggle('menu-aberto', isOpen);
        navLinks.classList.toggle('menu-aberto', isOpen);
        menuToggle.setAttribute('aria-expanded', String(isOpen));
        menuToggle.setAttribute(
            'aria-label',
            isOpen ? menuToggle.dataset.labelClose : menuToggle.dataset.labelOpen
        );
    }

    menuToggle.addEventListener('click', () => {
        setMenuOpen(menuToggle.getAttribute('aria-expanded') !== 'true');
    });

    navLinks.addEventListener('click', (event) => {
        if (event.target instanceof Element && event.target.closest('a')) {
            setMenuOpen(false);
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && menuToggle.getAttribute('aria-expanded') === 'true') {
            setMenuOpen(false);
            menuToggle.focus();
        }
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 820) setMenuOpen(false);
    });
}