# Troubleshooting — ucloud-newman-runner

## Problemas Comuns e Soluções

- **Template Jinja2 não encontrado**
  - Certifique-se de instalar via pip (`pip install ucloud-newman-runner`) e usar o comando global.
  - Para desenvolvimento, o runner faz fallback automático para FileSystemLoader.
  - Verifique se o template está presente em `src/runner/templates/`.

- **Erro ao enviar e-mail (Mailjet)**
  - Verifique se as variáveis `MAILJET_API_KEY` e `MAILJET_API_SECRET` estão corretas.
  - Confirme a conectividade com a API do Mailjet.
  - Verifique se o HTML gerado está bem formado.

- **Permissão de escrita nos relatórios**
  - Garanta permissão de escrita no diretório de destino (`results/`, `reports/`).
  - Se usar Docker, monte o volume com permissões adequadas.

- **Newman não encontrado**
  - Instale Node.js 18.12+.
  - Instale Newman e newman-reporter-htmlextra globalmente:
    ```bash
    nvm install 18.12
    nvm use 18.12
    npm install -g newman newman-reporter-htmlextra
    ```

- **Problemas de ambiente virtual**
  - Ative o virtualenv antes de rodar comandos Python.
  - Use `which python` e `which ucloud-newman-runner` para garantir que está usando o ambiente correto.

- **Debug detalhado**
  - Rode com variáveis de ambiente de debug:
    ```bash
    export LOG_LEVEL=DEBUG
    ucloud-newman-runner ...
    ```
  - Consulte os logs em `results/<id>/logs/` para detalhes de execução.

- **Outros erros**
  - Consulte o arquivo de log gerado para mensagens detalhadas.
  - Abra uma issue no GitHub com o erro completo e contexto. 