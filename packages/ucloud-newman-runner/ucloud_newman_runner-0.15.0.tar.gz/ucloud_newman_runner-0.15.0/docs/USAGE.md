# Guia de Uso — ucloud-newman-runner

## Execução Local (CLI)

```bash
ucloud-newman-runner --run \
  --collection ./colecao.json \
  --environment ./env.json \
  --destination ./results/ \
  --mailjet-api-key <API_KEY> \
  --mailjet-api-secret <API_SECRET> \
  --send-email-to email@dominio.com
```

## Execução via Docker

```bash
docker run --rm -v $(pwd):/data ucloudservices/ucloud-newman-runner:latest \
  --run --collection /data/colecao.json --environment /data/env.json --destination /data/results ...
```

## Parâmetros CLI

| Parâmetro                | Descrição                                              |
|-------------------------|-------------------------------------------------------|
| --run                   | Executa o runner de testes                            |
| --collection            | Caminho(s) para coleções Postman (.json)              |
| --environment           | Caminho para ambiente Postman (.json)                 |
| --destination           | Diretório base dos resultados                         |
| --type                  | Formatos de saída: table, csv, plaintext              |
| --mailjet-api-key       | API Key do Mailjet (opcional)                         |
| --mailjet-api-secret    | API Secret do Mailjet (opcional)                      |
| --send-email-to         | Lista de e-mails de destino (vírgula)                 |
| --client-name           | Nome do cliente (opcional, para personalização)       |
| --interactive           | Instala dependências Node/Newman se necessário        |

## Variáveis de Ambiente

Todos os parâmetros podem ser definidos por variável de ambiente:

| Variável de Ambiente   | Equivalente CLI           |
|-----------------------|---------------------------|
| RUNNER_ID             | --id                      |
| RUNNER_TYPE           | --type                    |
| RUNNER_COLLECTION     | --collection              |
| RUNNER_ENVIRONMENT    | --environment             |
| RUNNER_DESTINATION    | --destination             |
| MAILJET_API_KEY       | --mailjet-api-key         |
| MAILJET_API_SECRET    | --mailjet-api-secret      |
| SEND_EMAIL_TO         | --send-email-to           |
| CLIENT_NAME           | --client-name             |

## Integração em CI/CD

- Adicione o comando de execução no seu pipeline (GitHub Actions, GitLab CI, etc).
- Exemplo para GitHub Actions:

```yaml
- name: Run API Tests
  run: |
    pip install ucloud-newman-runner
    ucloud-newman-runner --run --collection ./colecao.json --environment ./env.json --destination ./results/
```

## Exemplos Avançados

- Executar múltiplas coleções:
  ```bash
  ucloud-newman-runner --run --collection ./col1.json --collection ./col2.json ...
  ```
- Usar variáveis de ambiente:
  ```bash
  export MAILJET_API_KEY=xxxx
  export MAILJET_API_SECRET=yyyy
  ucloud-newman-runner --run --collection ./colecao.json ...
  ```

## Dicas
- O runner cria diretórios automaticamente.
- O relatório HTML é salvo em `results/<id>/artifacts/html/`.
- Logs detalhados ficam em `results/<id>/logs/`.
- Para troubleshooting, consulte o arquivo [TROUBLESHOOTING.md](TROUBLESHOOTING.md). 