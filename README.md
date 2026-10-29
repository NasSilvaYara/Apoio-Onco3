# Plataforma de Apoio a Mulheres com Câncer

Plataforma web que centraliza instituições, ONGs e hospitais de apoio a mulheres com câncer de mama, permitindo buscar serviços por localização e tipo de apoio — como bancos de perucas, bancos de lenços e apoio psicológico. O sistema não possui estoque próprio nem presta os serviços diretamente; as informações de disponibilidade são de responsabilidade das instituições cadastradas.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Bootstrap](https://img.shields.io/badge/Bootstrap-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

## Destaques

- Busca de instituições com filtro por cidade e estado
- Pacientes e visitantes acessam sem precisar criar conta
- Instituições cadastram perfil, serviços, endereço e horários de atendimento
- Painel administrativo: aprovação/rejeição de cadastros, gestão de usuários e conteúdos
- Acessibilidade: navegação por teclado, contraste, leitores de tela, fontes ajustáveis e tradução

## Como rodar o projeto

## 3. Como Instalar e Rodar a Aplicação

### Pré-requisitos
- [Python](https://www.python.org/) 3.12 ou superior
- [Git](https://git-scm.com/) instalado
- O arquivo **`.env`**, enviado pela equipe em particular (contém as credenciais do banco)

Não é preciso instalar nenhum banco de dados na sua máquina.

### Passo 1: Clonar o repositório
```bash
git clone https://github.com/NasSilvaYara/Apoio-Onco3.git
cd Apoio-Onco3
```

### Passo 2: Criar e ativar o ambiente virtual
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
No Linux/macOS: `source .venv/bin/activate`

### Passo 3: Instalar as dependências
```powershell
pip install -r requirements.txt
```

### Passo 4: Colocar o arquivo `.env`
Salve o `.env` recebido da equipe **na raiz do projeto**, na mesma pasta do `manage.py`.

- O nome do arquivo é exatamente `.env` (não `.env.txt`).
- O `.env` nunca vai para o GitHub: ele está no `.gitignore`. Não o envie em commits, issues ou grupos públicos.
- O arquivo `.env.example` mostra quais variáveis existem, sem os valores.

### Passo 5: Aplicar as migrações
```powershell
python manage.py migrate
```
O banco é compartilhado pela equipe. Se estiver tudo em dia, a resposta é `No migrations to apply`.

### Passo 6: Iniciar o servidor
```powershell
python manage.py runserver
```
Abra o navegador em http://127.0.0.1:8000/

### Problemas comuns

| Erro | Causa provável |
|---|---|
| `Configure DJANGO_SECRET_KEY no ambiente` | O `.env` não está na raiz do projeto, ou está com outro nome |
| `connection timeout expired` | `PGHOST` do `.env` errado ou vazio |
| `password authentication failed` | `PGUSER` ou `PGPASSWORD` incorretos |

---

## Equipe

| Nome | LinkedIn |
|---|---|
| Nicoly Santos | [linkedin.com/in/nicoly-santos](https://linkedin.com/in/nicoly-santos) |
| Livia Schendroski | [linkedin.com/in/livia-schendroski](https://linkedin.com/in/livia-schendroski) |
| Yara Nascimento | [linkedin.com/in/yara-nascimento](https://linkedin.com/in/yara-nascimento) |

Projeto Interdisciplinar — 3º Semestre

---
