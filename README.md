<div align="center">

  <img src="static/img/logo-inteira.png" alt="Logo Plataforma de Apoio a Mulheres com Câncer" width="160" />

  <h1>Plataforma de Apoio a Mulheres com Câncer</h1>

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
</div>

---

## 1. Introdução e Visão de Negócio

A **Plataforma de Apoio a Mulheres com Câncer** é uma solução web desenvolvida como Projeto Interdisciplinar (3º Semestre) que tem como principal objetivo centralizar e facilitar o acesso a instituições, ONGs, redes de apoio e hospitais voltados ao auxílio de mulheres com câncer de mama.

### O Problema & A Solução
Frequentemente, pacientes diagnosticadas enfrentam uma jornada solitária e fragmentada para descobrir onde encontrar serviços essenciais de suporte (como bancos de perucas, bancos de lenços, atendimento psicológico, grupos de apoio e assistência jurídica/social). 

A plataforma resolve isso permitindo:
- **Busca Geolocalizada e por Categoria:** Pacientes e visitantes encontram serviços de forma rápida filtrando por localização (cidade/estado) e tipo de apoio necessário, **sem a necessidade de criar conta**.
- **Autogestão para Instituições:** Organizações cadastradas podem gerenciar seus próprios perfis, atualizar endereços, horários de atendimento e os serviços ofertados.
- **Transparência:** O sistema atua como um agregador/diretório; ele não possui estoque próprio nem presta serviços diretamente, sendo as informações de disponibilidade de responsabilidade das instituições cadastradas.

---

## 2. Tecnologias Utilizadas

O projeto foi construído utilizando as seguintes tecnologias e ferramentas:

* **Linguagem:** `Python 3.x`
* **Framework Web:** `Django` (MVT - Model-View-Template / ORM)
* **Banco de Dados Relacional:** `PostgreSQL`
* **Front-end:** `HTML5`, `CSS3`, `JavaScript`
* **Controle de Versão:** `Git` e `GitHub`

---

## 3. Como Instalar e Rodar a Aplicação

Siga o passo a passo detalhado abaixo para configurar e executar o projeto em sua máquina local.

### Pré-requisitos
- [Python](https://python.org) (Versão 3.10 ou superior recomendada)
- [Git](https://git-scm.com) instalado
- Servidor [PostgreSQL](https://postgresql.org) rodando localmente ou em nuvem

---

### Passo 1: Clonar o Repositório
Abra o seu terminal (PowerShell, Git Bash ou terminal Linux/macOS) e execute:
```bash
git clone https://github.com
cd Apoio-Onco3
```

### Passo 2: Criar e Ativar o Ambiente Virtual
O ambiente virtual isola as dependências do projeto. Execute os comandos de acordo com o seu sistema operacional:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Passo 3: Instalar as Dependências
Com o ambiente virtual activated, instale as bibliotecas necessárias listadas no arquivo:
```powershell
pip install -r requirements.txt
```

### Passo 4: Configurar o Banco de Dados e Variáveis de Ambiente
Crie um banco de dados vazio no seu PostgreSQL.

Crie um arquivo `.env` na raiz do projeto baseando-se no exemplo (`.env.example`) ou configure as credenciais do seu banco PostgreSQL conforme descrito em `docs/BANCO_DE_DADOS.md`.

### Passo 5: Executar as Migrações
Aplique a estrutura do banco de dados e crie a conta de acesso ao painel de controle:
```powershell
python manage.py migrate
```

### Passo 6: Iniciar o Servidor de Desenvolvimento
Inicie o servidor local do Django:
```powershell
python manage.py runserver
```

Abra o seu navegador e acesse: http://127.0.0

Execute os testes com `python manage.py test`. A suíte exige um serviço PostgreSQL acessível com as credenciais configuradas no `.env`.

---

## 4. Exemplos de Uso

1. **Busca de Apoio Psicológico:**
   > A usuária acessa a página pública, filtra por sua cidade e seleciona a categoria *"Apoio Psicológico"*. O sistema exibe instantaneamente as ONGs e hospitais disponíveis com telefone, endereço e horário.

2. **Cadastro de Nova Instituição:**
   > Uma organização preenche o formulário de cadastro com seu endereço e serviços. O registro fica pendente até ser aprovado pela administração no painel de controle.

---

## Equipe

| Nome | LinkedIn |
|---|---|
| Nicoly Santos | [://linkedin.com](https://://linkedin.com) |
| Livia Schendroski | [://linkedin.com](https://://linkedin.com) |
| Yara Nascimento | [://linkedin.com](https://://linkedin.com) |

Projeto Interdisciplinar — 3º Semestre

---
*Projeto acadêmico.*
