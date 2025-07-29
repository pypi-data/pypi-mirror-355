# Estrutura do Projeto — ucloud-newman-runner

```
ucloud-newman-runner/
├── src/runner/           # Core do runner (run.py, config.py, emailer.py, reporting.py)
│   ├── templates/        # Templates Jinja2 para relatórios HTML
├── tests/                # Testes automatizados (pytest)
├── requirements.txt      # Dependências principais
├── pyproject.toml        # Configuração de build PyPI
├── .ci/                  # Dockerfile, entrypoint, CI/CD
├── README.md             # Documentação principal
├── LICENSE               # Licença MIT
├── docs/                 # Documentação adicional
```

## Descrição das Pastas

- **src/runner/**: Código principal do runner, incluindo lógica de execução, configuração, geração de relatórios e envio de e-mail.
- **src/runner/templates/**: Templates Jinja2 usados para gerar relatórios HTML customizados.
- **tests/**: Testes unitários e de integração, usando pytest.
- **.ci/**: Arquivos de automação para CI/CD e Docker.
- **docs/**: Guias, exemplos e documentação complementar.

## Estrutura de Resultados de Execução

```
results/<id>/
  artifacts/
    html/      # Relatórios HTML do Newman
    json/      # Relatórios JSON detalhados do Newman
    newman_summary.json  # Resumo global da execução
  logs/
    newman_tests.log     # Log do runner Python
```

> Para detalhes sobre cada módulo, consulte as docstrings no código-fonte ou [docs/USAGE.md](USAGE.md). 