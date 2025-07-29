# Guia de Contribuição

Obrigado por considerar contribuir com o `ucloud-newman-runner`! Este documento fornece diretrizes e padrões para contribuições.

## Código de Conduta

Este projeto segue um Código de Conduta. Ao participar, você concorda em seguir suas diretrizes.

## Como Contribuir

1. **Fork e Clone**
   ```bash
   git clone https://github.com/seu-usuario/ucloud-newman-runner.git
   cd ucloud-newman-runner
   ```

2. **Configurar Ambiente**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pre-commit install
   ```

3. **Criar Branch**
   ```bash
   git checkout -b feature/sua-feature
   ```

4. **Desenvolver**
   - Siga os padrões de código
   - Adicione testes
   - Atualize a documentação
   - Use mensagens de commit semânticas

5. **Testar**
   ```bash
   pytest
   pytest --cov=src tests/
   ```

6. **Submeter PR**
   - Descreva as mudanças
   - Referencie issues relacionadas
   - Aguarde review

## Padrões de Código

### Python
- Use Python 3.9+
- Siga PEP 8
- Use type hints
- Documente usando docstrings
- Mantenha 100% de cobertura

### Commits
Use mensagens semânticas:
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `test:` Testes
- `refactor:` Refatoração
- `style:` Formatação
- `chore:` Manutenção

### Testes
- Escreva testes unitários
- Escreva testes de integração
- Use fixtures quando apropriado
- Mock dependências externas

### Documentação
- Mantenha o README atualizado
- Documente novas funcionalidades
- Atualize o CHANGELOG
- Inclua exemplos de uso

## Estrutura do Projeto

```
ucloud-newman-runner/
├── src/                    # Código fonte
│   ├── runner/            # Core da aplicação
│   └── utils/             # Utilitários
├── tests/                  # Testes
├── docs/                   # Documentação
└── examples/               # Exemplos
```

## Fluxo de Desenvolvimento

1. **Planejamento**
   - Crie uma issue
   - Discuta a implementação
   - Defina critérios de aceitação

2. **Desenvolvimento**
   - Siga TDD quando possível
   - Mantenha commits pequenos
   - Execute os hooks pre-commit

3. **Review**
   - Auto-review seu código
   - Responda aos comentários
   - Faça ajustes necessários

4. **Merge**
   - Rebase com main
   - Resolva conflitos
   - Aguarde aprovação

## Dicas

- Use `black` para formatação
- Use `isort` para imports
- Use `mypy` para type checking
- Use `flake8` para linting
- Use `bandit` para segurança

## Suporte

- Abra uma issue para dúvidas
- Use discussões para ideias
- Participe do canal no Slack 