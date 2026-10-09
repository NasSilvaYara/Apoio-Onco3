// Máscara: (00) 0000-0000 ou (00) 00000-0000
function formatarTelefone(valor) {
  const d = valor.replace(/\D/g, '').slice(0, 11);
  return d
    .replace(/^(\d{2})(\d)/, '($1) $2')
    .replace(d.length > 10 ? /(\d{5})(\d)/ : /(\d{4})(\d)/, '$1-$2');
}

for (const id of ['telefone', 'whatsapp']) {
  const campo = document.getElementById(id);
  campo.value = formatarTelefone(campo.value);
  campo.addEventListener('input', () => {
    campo.value = formatarTelefone(campo.value);
  });
}

// Instagram: garante o @ no começo quando a pessoa digita algo
const instagram = document.getElementById('instagram');
instagram.addEventListener('blur', () => {
  const valor = instagram.value.trim();
  if (valor && !valor.startsWith('@')) instagram.value = '@' + valor;
});