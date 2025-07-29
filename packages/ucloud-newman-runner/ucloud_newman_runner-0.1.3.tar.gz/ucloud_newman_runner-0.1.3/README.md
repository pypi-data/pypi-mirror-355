# ucloud-newman-runner

[![PyPI version](https://img.shields.io/pypi/v/ucloud-newman-runner.svg)](https://pypi.org/project/ucloud-newman-runner/)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI](https://github.com/ucloudbr/ucloud-newman-runner/actions/workflows/python-ci.yml/badge.svg)](https://github.com/ucloudbr/ucloud-newman-runner/actions)

Automação de testes de API com Newman (Postman CLI), geração de relatórios HTML customizados e envio automático por e-mail.

---

## 🚀 Visão Geral

O `ucloud-newman-runner` executa coleções Postman via Newman, gera relatórios HTML com template customizável e envia o HTML gerado diretamente no corpo do e-mail para os destinatários configurados.

- **Execução automatizada de coleções Postman**
- **Relatório HTML customizado** (via `custom-template.hbs`)
- **Envio automático do HTML por e-mail** (Mailjet)
- **Geração opcional de CSV e TXT para integração**
- **Pronto para CI/CD, pipelines e uso local**

---

## 📦 Stack e Pré-requisitos

- **Python** 3.9+
- **Node.js** 18.12+ (use nvm)
- **Newman** e **newman-reporter-htmlextra** (globais)
- **Mailjet** (opcional, para envio de e-mail)
- **pnpm** (para dependências Node)

### Instalação rápida

```bash
nvm install 18.12
nvm use 18.12
npm install -g pnpm newman newman-reporter-htmlextra
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pnpm install
```

---

## 📁 Estrutura do Projeto

```
ucloud-newman-runner/
├── src/runner/run.py           # Orquestra execução e envio de e-mail
├── src/runner/emailer.py       # Envia o HTML gerado por e-mail
├── templates/custom-template.hbs # Template Handlebars para HTML do Newman
├── results/<id>/artifacts/html/ # Relatórios HTML gerados
├── ...
```

---

## ⚙️ Como Funciona

1. **Executa o Newman** usando o template customizado:
   ```bash
   newman run <colecao.json> -e <ambiente.json> \
     -r htmlextra --reporter-htmlextra-template templates/custom-template.hbs \
     --reporter-htmlextra-export results/<id>/artifacts/html/relatorio.html
   ```
2. **O runner Python lê o HTML gerado** e envia como corpo do e-mail (Mailjet).
3. **Não há montagem de HTML adicional**: o que o Newman gera é o que o destinatário recebe.

---

## 📨 Envio de E-mail (Mailjet)

- O runner lê o HTML gerado e envia para os destinatários configurados.
- O assunto pode ser customizado com o nome do cliente.
- Não há mais uso de `report-template.html` ou qualquer template intermediário.

### Exemplo de envio automático (via runner):

```bash
python src/runner/run.py --run \
  --id exec01 \
  --collection postman/lekto_admin.postman_collection.json \
  --environment postman/env_stg.postman_environment.json \
  --mailjet-api-key <SUA_API_KEY> \
  --mailjet-api-secret <SEU_API_SECRET> \
  --send-email-to email1@dominio.com,email2@dominio.com
```

---

## 🛡️ Boas Práticas

- **Mantenha o CSS inline** no `custom-template.hbs` para máxima compatibilidade com e-mail.
- **Evite fontes externas, JS ou links remotos** no template.
- **Teste o HTML em diferentes clientes de e-mail** (Gmail, Outlook, etc).
- **Personalize o template** para o branding do seu time/empresa.

---

## 📊 Relatórios e Métricas

- **HTML**: Relatório detalhado, visual e pronto para e-mail
- **CSV/TXT**: Geração opcional para integração
- **Resumo de métricas**: Total de requisições, falhas, assertions, sucesso (%)

---

## 🐳 Docker e CI/CD

- Imagem Docker pronta para CI/CD
- Entrypoint automatizado
- Exemplo:
  ```bash
  docker build -f .ci/Dockerfile -t ucloud-newman-runner .
  docker run --rm -v $(pwd):/ucloud ucloud-newman-runner
  ```

---

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Crie um Pull Request

---

## 📄 Licença

MIT. Veja o arquivo LICENSE.

---

## 🔍 Troubleshooting

- **E-mail não chega**: verifique credenciais do Mailjet, caixa de spam e se o HTML está bem formado.
- **HTML quebrado no e-mail**: revise o template para CSS inline e compatibilidade.
- **Erro de permissão**: garanta que o runner tem acesso de leitura ao HTML gerado.

---

## 🎯 Resumo

- **1 template, 1 HTML, 1 e-mail**: simples, robusto e fácil de manter.
- **O que o Newman gera é o que o destinatário recebe.**
- **Foco em automação, clareza e compatibilidade.**

---

## 🧭 Visão Geral

O `ucloud-newman-runner` é uma solução SaaS multi-cliente desenvolvida pela UCloud Services para automação de testes de API usando Newman (CLI do Postman). Ele foi projetado para múltiplos clientes, squads e times de QA automatizarem fluxos de testes e receberem relatórios centralizados, sem dependência de ambiente ou stack específica.

- Execução automatizada de coleções Postman para múltiplos clientes
- Geração de relatórios detalhados em HTML, CSV, plaintext e envio de email
- Integração contínua com pipelines CI/CD e Docker
- Multi-cliente/multi-tenant (parametrização por variáveis de ambiente)

---

## 🛠️ Stack e Ambiente

- **Python** 3.9+
- **Node.js** 18.12+ (para Newman)
- **Newman** (CLI do Postman) e newman-reporter-htmlextra
- **Mailjet** (opcional, para envio de email)
- **Docker** (imagem pronta para CI/CD)
- **pytest**, **black**, **isort**, **flake8**, **mypy** (dev)

### Instalação rápida

```bash
# Clone o repositório
$ git clone https://github.com/ucloudbr/ucloud-newman-runner.git
$ cd ucloud-newman-runner

# Crie e ative o ambiente virtual
$ python -m venv .venv
$ source .venv/bin/activate

# Instale as dependências
$ pip install -r requirements.txt
```

---

## 📁 Estrutura de Diretórios do Projeto

```
ucloud-newman-runner/
├── .ci/                # CI/CD, Dockerfile, entrypoint
│   ├── Dockerfile
│   ├── docker-entrypoint.sh
│   └── .dockerignore
├── src/                # Código fonte principal
│   ├── runner/        # Core do runner (run_newman_tests.py, send_email.py)
│   └── utils/         # Utilitários
├── templates/          # Templates de email e relatórios
│   ├── email/
│   │   └── report-template.html
│   ├── custom-template.hbs
│   └── email-template.html
├── tests/              # Testes automatizados (pytest)
├── docs/               # Documentação e guias
│   └── CONTRIBUTING.md
├── examples/           # Exemplos de uso
├── reports/            # (opcional) Relatórios gerados
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── CHANGELOG.md
├── LICENSE
└── README.md
```

### Estrutura de Resultados de Execução

```
results/<id>/
  artifacts/
    html/      # Relatórios HTML do Newman
    json/      # Relatórios JSON detalhados do Newman
    newman_summary.json  # Resumo global da execução
  logs/
    newman_tests.log     # Log do runner Python
```
> **Nota:** Pastas `csv/` e `text/` estão previstas, mas **ainda não são geradas**.

---

## 🚀 Execução Rápida

### Pré-requisitos
- Python 3.9+
- Node.js 18.12+ e Newman (`npm install -g newman newman-reporter-htmlextra`)
- Coleções Postman em formato JSON
- (Opcional) Conta Mailjet para envio de emails

### Comando Básico

```bash
python main.py \
  --id tmp01 \
  --type table \
  --environment ./postman/env_stg.postman_environment.json \
  --collection ./postman/lekto_admin.postman_collection.json \
  --destination ./results/tmp01/
```

### Comando com Email (planejado)

```bash
python main.py \
  --id tmp01 \
  --type table \
  --environment ./postman/env_stg.postman_environment.json \
  --collection ./postman/lekto_admin.postman_collection.json \
  --destination ./results/tmp01/ \
  --mailjet-api-key <SUA_API_KEY> \
  --mailjet-api-secret <SEU_API_SECRET> \
  --send-email-to email1@dominio.com,email2@dominio.com
```
> **Atenção:** O envio de email e geração de CSV/plaintext ainda **não estão implementados**.

### Precedência dos Parâmetros

1. **Variável de ambiente** (ex: `MAILJET_API_KEY`)
2. **Parâmetro CLI** (ex: `--mailjet-api-key`)
3. **Valor default** (se aplicável)

---

## ⚙️ Parâmetros Disponíveis

| Parâmetro CLI           | Variável de Ambiente      | Obrigatório | Descrição |
|------------------------|--------------------------|-------------|-----------|
| --id                   | RUNNER_ID                | Sim         | Identificador único da execução (ex: tmp01) |
| --type                 | RUNNER_TYPE              | Não         | Saída: table (CSV, plaintext planejados) |
| --collection           | RUNNER_COLLECTION        | Não         | Caminho(s) para coleções Postman (.json); se não informar, busca arquivos automaticamente |
| --environment          | RUNNER_ENVIRONMENT       | Não         | Arquivo de ambiente Postman (.postman_environment.json) |
| --destination          | RUNNER_DESTINATION       | Não         | Diretório base dos resultados |
| --mailjet-api-key      | MAILJET_API_KEY          | Não         | API Key do Mailjet (opcional) |
| --mailjet-api-secret   | MAILJET_API_SECRET       | Não         | API Secret do Mailjet (opcional) |
| --send-email-to        | SEND_EMAIL_TO            | Não         | Lista de emails de destino, separados por vírgula (opcional) |
| --interactive          | N/A                      | Não         | Modo interativo: instala o newman se necessário (opcional) |

---

## 📊 Relatórios e Métricas

- **HTML**: Relatório detalhado com métricas e resultados (implementado)
- **CSV/Plaintext/Table**: (planejado)
- **Email**: Sumário executivo enviado automaticamente (planejado)

### Métricas Coletadas
- Total de requisições
- Taxa de sucesso
- Tempo de execução
- Cobertura de assertions
- Falhas e erros
- Cliente/Projeto executado

---

## 🐳 Docker e CI/CD

- Imagem Docker pronta em `.ci/Dockerfile`
- Entrypoint automatizado: `.ci/docker-entrypoint.sh`
- Exemplo de uso:

```bash
docker build -f .ci/Dockerfile -t ucloud-newman-runner .
docker run --rm -v $(pwd):/ucloud ucloud-newman-runner
```

---

## 🧪 Testes e Qualidade

- Testes automatizados em `tests/` (pytest)
- Linting: black, isort, flake8, mypy
- Pre-commit hooks configurados
- Cobertura de código: pytest-cov

### Como rodar os testes

Execute todos os testes unitários e de integração com:

```bash
pytest --maxfail=1 --disable-warnings -v
```

Ou rode um teste específico:

```bash
pytest tests/test_config.py -v
```

### Cobertura de código

Para gerar o relatório de cobertura:

```bash
pytest --cov=src --cov-report=term-missing
```

O relatório mostrará quais arquivos e linhas ainda não estão cobertos por testes.

### Boas práticas
- Use mocks para dependências externas (subprocessos, requests, arquivos).
- Prefira nomes de teste descritivos e siga o padrão `test_nome_do_modulo.py`.
- Teste casos de sucesso, falha e edge cases.
- Limpe arquivos temporários criados nos testes.
- Contribua com novos testes para cada feature ou correção.

### Integração Contínua (CI) - Exemplo GitHub Actions

Para rodar os testes automaticamente a cada push/pull request, adicione o seguinte workflow em `.github/workflows/python-ci.yml`:

```yaml
name: Python CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m venv .venv
          source .venv/bin/activate
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests
        run: |
          source .venv/bin/activate
          pytest --cov=src --cov-report=term-missing
```

---

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

Veja o [Guia de Contribuição](docs/CONTRIBUTING.md) para detalhes, padrões de código, mensagens semânticas e fluxo de desenvolvimento.

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 🔍 Troubleshooting

### Problemas Comuns

1. **Erro de Permissão nos Relatórios**
   - Verifique as permissões do diretório `reports/`
   - Certifique-se que o container tem acesso de escrita

2. **Falha no Envio de Email**
   - Verifique as credenciais do Mailjet
   - Confirme a conectividade com a API
   - (Funcionalidade planejada)

3. **Erro na Execução do Newman**
   - Valide o formato das coleções Postman
   - Verifique a conectividade com as APIs testadas

---

## 📚 Documentação Adicional

- [Guia de Contribuição](docs/CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## 🎯 Objetivo

O `ucloud-newman-runner` é uma solução SaaS multi-cliente desenvolvida pela UCloud Services para automação de testes de API usando Newman (CLI do Postman). Ele foi projetado para atender múltiplos clientes simultaneamente, permitindo que empresas, squads e times de QA automatizem seus fluxos de testes e recebam relatórios centralizados, sem dependência de ambiente ou stack específica.

- Execução automatizada de coleções Postman para múltiplos clientes
- Geração de relatórios detalhados em HTML, CSV, plaintext e tabela
- Envio automático de relatórios por email via Mailjet
- Integração contínua com pipelines CI/CD
- Execução isolada em containers Docker ou ambiente local

## 🌐 Multi-cliente e Multi-tenant

O runner foi pensado para uso em ambientes SaaS, consultorias, squads de QA e empresas que atendem múltiplos projetos ou clientes. Cada execução pode ser parametrizada por variáveis de ambiente, facilitando a integração com diferentes contextos, times e domínios.

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.9+
- Newman instalado globalmente (`npm install -g newman`)
- Conta Mailjet para envio de emails (opcional)
- Coleções Postman em formato JSON

### Instalação

```bash
# Clone o repositório
$ git clone https://github.com/ucloudbr/ucloud-newman-runner.git
$ cd ucloud-newman-runner

# Crie e ative o ambiente virtual
$ python -m venv .venv
$ source .venv/bin/activate

# Instale as dependências
$ pip install -r requirements.txt
```

### Execução Básica

```bash
python src/runner/run_newman_tests.py \
  --id tmp01 \
  --type table,csv,plaintext \
  --environment ./postman/env_stg.postman_environment.json \
  --collection ./postman/lekto_admin.postman_collection.json \
  --destination ./results/tmp01/
```

### Execução com Envio de Email

```bash
python src/runner/run_newman_tests.py \
  --id tmp01 \
  --type table,csv,plaintext \
  --environment ./postman/env_stg.postman_environment.json \
  --collection ./postman/lekto_admin.postman_collection.json \
  --destination ./results/tmp01/ \
  --mailjet-api-key <SUA_API_KEY> \
  --mailjet-api-secret <SEU_API_SECRET> \
  --send-email-to email1@dominio.com,email2@dominio.com
```

### Precedência dos Parâmetros

> **Atenção:** Para todos os parâmetros, a precedência é:
> 1. **Variável de ambiente** (ex: `MAILJET_API_KEY`)
> 2. **Parâmetro CLI** (ex: `--mailjet-api-key`)
> 3. **Valor default** (se aplicável)

Exemplo:
```bash
export MAILJET_API_KEY=xxxx
python src/runner/run_newman_tests.py --mailjet-api-key yyyy
# O runner usará o valor de MAILJET_API_KEY do CLI, ignorando o ambiente.
```

### Parâmetros Disponíveis

| Parâmetro CLI           | Variável de Ambiente      | Obrigatório | Descrição |
|------------------------|--------------------------|-------------|-----------|
| --id                   | RUNNER_ID                | Sim         | Identificador único da execução (ex: tmp01) |
| --type                 | RUNNER_TYPE              | Não         | Saída: table, csv, plaintext (inclusive múltiplos) |
| --collection           | RUNNER_COLLECTION        | Não         | Caminho(s) para coleções Postman (.json); se não informar, varre recursivamente a pasta atual procurando arquivos de coleção |
| --environment          | RUNNER_ENVIRONMENT       | Não         | Arquivo de ambiente Postman (.postman_environment.json) |
| --destination          | RUNNER_DESTINATION       | Não         | Diretório base dos resultados (ex: ./results/tmp01/) |
| --mailjet-api-key      | MAILJET_API_KEY          | Não         | API Key do Mailjet (opcional) |
| --mailjet-api-secret   | MAILJET_API_SECRET       | Não         | API Secret do Mailjet (opcional) |
| --send-email-to        | SEND_EMAIL_TO            | Não         | Lista de emails de destino, separados por vírgula (opcional) |
| --interactive          | N/A                      | Não         | Modo interativo: instala o newman se necessário (opcional) |

## 📁 Estrutura de Diretórios de Resultados

```
results/<id>/
  artifacts/
    html/      # Relatórios HTML do Newman
    text/      # Relatórios TXT do Newman
    csv/      # Relatórios CSV do Newman
    json/      # Relatórios JSON detalhados do Newman
    newman_summary.json  # Resumo global da execução
  logs/
    newman_tests.log     # Log do runner Python
```

## 📊 Relatórios e Métricas

- **HTML**: Relatório detalhado com métricas e resultados
- **CSV/Plaintext/Table**: (em breve) formatos alternativos para integração e automação
- **Email**: Sumário executivo enviado automaticamente (opcional)

### Métricas Coletadas

- Total de requisições
- Taxa de sucesso
- Tempo de execução
- Cobertura de assertions
- Falhas e erros
- Cliente/Projeto executado

## 🛡️ Robustez e Flexibilidade

- O runner cria automaticamente todos os diretórios necessários para relatórios e artefatos, mesmo que você informe caminhos novos ou aninhados via `--destination`.
- Aceita caminhos relativos ou absolutos para o destino dos relatórios.
- Parâmetro `--collection` permite especificar uma ou mais coleções Postman; se não informado, busca automaticamente arquivos `*.postman_collection.json` no diretório padrão.
- Parâmetro `--environment` permite especificar o arquivo de ambiente Postman (`.postman_environment.json`) para execuções customizadas.
- Tratamento de erros amigável: mensagens claras para diretórios, coleções ou permissões ausentes.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

### Padrões de Código

- Siga a PEP 8
- Use type hints
- Documente funções e classes
- Mantenha 100% de cobertura de testes
- Use mensagens de commit semânticas

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🔍 Troubleshooting

### Problemas Comuns

1. **Erro de Permissão nos Relatórios**
   - Verifique as permissões do diretório `reports/`
   - Certifique-se que o container tem acesso de escrita

2. **Falha no Envio de Email**
   - Verifique as credenciais do Mailjet
   - Confirme a conectividade com a API

3. **Erro na Execução do Newman**
   - Valide o formato das coleções Postman
   - Verifique a conectividade com as APIs testadas

## 📚 Documentação Adicional

- [Guia de Contribuição](docs/CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Documentação da API](docs/API.md)
- [Guia de Desenvolvimento](docs/DEVELOPMENT.md)

## 📦 Módulos e Responsabilidades

| Módulo                        | Responsabilidade Principal                                              |
|-------------------------------|------------------------------------------------------------------------|
| `src/runner/run_newman_tests.py` | Orquestra execução, logging, parsing de argumentos, fluxo principal    |
| `src/runner/config.py`           | Parsing/validação de config, precedência CLI/ENV, dataclass de config |
| `src/runner/reporting.py`        | Geração de relatórios CSV, plaintext/table                            |
| `src/runner/emailer.py`          | Envio de email via Mailjet, template, validação de parâmetros         |
| `templates/email/`               | Templates HTML para email                                             |
| `tests/`                         | Testes unitários e integração                                         |
| `.ci/`                           | Dockerfile, entrypoint, CI/CD                                         |

## 🔗 Execução como CLI global

Você pode executar o runner de duas formas:

### 1. Tornando o main.py executável

```bash
chmod +x main.py
./main.py --id tmp01 ...
```

### 2. Instalando como comando global via pyproject.toml

Adicione ao seu `pyproject.toml`:

```toml
[project.scripts]
ucloud-newman-runner = "src.runner.run:main"
```

Depois, instale localmente:

```bash
pip install .
```

E execute de qualquer lugar:

```bash
ucloud-newman-runner --id tmp01 ...
```

Ambos os métodos facilitam a execução e integração do runner em pipelines, scripts e ambientes de automação.

## 📦 Instalação via pip

A forma mais simples de instalar o runner é via PyPI:

```bash
pip install ucloud-newman-runner
```

Ou, para instalar a partir do código fonte local:

```bash
pip install .
```

Após a instalação, o comando `ucloud-newman-runner` estará disponível globalmente.

## 📚 Documentação de API (Uso Programático)

Além do uso via CLI, você pode importar e usar os módulos principais do runner em seus próprios scripts Python:

```python
from src.runner.run import run_newman
from src.runner.config import parse_config

config = parse_config()  # ou crie manualmente um objeto Config
success = run_newman(config)
```

Você também pode importar utilitários para geração de relatórios ou envio de email:

```python
from src.runner.reporting import write_csv_report, write_plaintext_table
from src.runner.emailer import send_email_report
```

Consulte as docstrings dos módulos para detalhes de parâmetros e exemplos avançados. 