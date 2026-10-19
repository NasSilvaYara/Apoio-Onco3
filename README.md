## 🎗️ Plataforma de Apoio a Mulheres com Câncer

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

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
* **Banco de Dados Relacional:** `MySQL`
* **Front-end:** `HTML5`, `CSS3`, `JavaScript`
* **Controle de Versão:** `Git` e `GitHub`

---

## 3. Como Instalar e Rodar a Aplicação

Siga o passo a passo detalhado abaixo para configurar e executar o projeto em sua máquina local.

### Pré-requisitos
- [Python](https://www.python.org/) (Versão 3.10 ou superior recomendada)
- [Git](https://git-scm.com/) instalado
- Servidor [MySQL](https://www.mysql.com/) rodando localmente ou em nuvem

---

### Passo 1: Clonar o Repositório
Abra o seu terminal (PowerShell, Git Bash ou terminal Linux/macOS) e execute:
```bash
git clone [https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git](https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git)
cd SEU-REPOSITORIO
```

### Passo 2: Criar e Ativar o Ambiente Virtual
O ambiente virtual isola as dependências do projeto. Execute os comandos de acordo com o seu sistema operacional:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
## Passo 3: Instalar as Dependências
Com o ambiente virtual ativado, instale as bibliotecas necessárias listadas no arquivo
```powershell
pip install -r requirements.txt
```
## Passo 4: Configurar o Banco de Dados e Variáveis de Ambiente
Crie um banco de dados vazio no seu MySQL.

Crie um arquivo .env na raiz do projeto baseando-se no exemplo (.env.example) ou configure as credenciais do seu banco MySQL conforme descrito em docs/BANCO_DE_DADOS.md.

## Passo 5: Executar as Migrações
Aplique a estrutura do banco de dados e crie a conta de acesso ao painel de controle:
```powershell
python manage.py migrate
```

## Passo 6: Iniciar o Servidor de Desenvolvimento
Inicie o servidor local do Django:
```powershell
python manage.py runserver
```

Abra o seu navegador e acesse: http://127.0.0.1:8000/

Execute os testes com `python manage.py test`. A suíte exige um serviço MySQL acessível com as credenciais configuradas no `.env`.

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
| Nicoly Santos | [linkedin.com/in/nicoly-santos](https://linkedin.com/in/nicoly-santos) |
| Livia Schendroski | [linkedin.com/in/livia-schendroski](https://linkedin.com/in/livia-schendroski) |
| Yara Nascimento | [linkedin.com/in/yara-nascimento](https://linkedin.com/in/yara-nascimento) |

Projeto Interdisciplinar — 3º Semestre

---
*Projeto acadêmico.*
