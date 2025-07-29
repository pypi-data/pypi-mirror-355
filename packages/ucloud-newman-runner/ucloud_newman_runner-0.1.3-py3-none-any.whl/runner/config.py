import os
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

def get_config_value(env_var: str, cli_value: Optional[str], default: Optional[str] = None) -> Optional[str]:
    """Retorna o valor de configuração com precedência: ENV > CLI > default.

    Args:
        env_var: Nome da variável de ambiente.
        cli_value: Valor passado via linha de comando.
        default: Valor padrão caso nenhum dos anteriores esteja definido.

    Returns:
        O valor de configuração encontrado, ou None.
    """
    return os.getenv(env_var) or cli_value or default

@dataclass
class Config:
    id_exec: str
    output_type: str
    collection: Optional[str]
    environment: Optional[str]
    destination: str
    mailjet_api_key: Optional[str]
    mailjet_api_secret: Optional[str]
    send_email_to: List[str]
    interactive: bool
    client_name: Optional[str]
    build_number: str = '--'
    commit_hash: str = '--'

    @property
    def base_dir(self) -> Path:
        """Retorna o diretório base da execução."""
        d = Path(self.destination).expanduser().resolve()
        return d / self.id_exec if self.id_exec else d
    @property
    def artifacts_html_dir(self) -> Path:
        """Retorna o diretório de artefatos HTML."""
        return self.base_dir / 'artifacts' / 'html'
    @property
    def artifacts_json_dir(self) -> Path:
        """Retorna o diretório de artefatos JSON."""
        return self.base_dir / 'artifacts' / 'json'
    @property
    def artifacts_dir(self) -> Path:
        """Retorna o diretório de artefatos."""
        return self.base_dir / 'artifacts'
    @property
    def logs_dir(self) -> Path:
        """Retorna o diretório de logs."""
        return self.base_dir / 'logs'
    @property
    def log_file(self) -> Path:
        """Retorna o caminho do arquivo de log principal."""
        return self.logs_dir / 'output.log'

def parse_config() -> Config:
    """Faz o parsing dos argumentos e variáveis de ambiente, validando obrigatórios.

    Returns:
        Config: Objeto de configuração preenchido.
    """
    parser = argparse.ArgumentParser(description="Runner de testes Newman UCloud")
    parser.add_argument('--destination', '-d', default='results', help='Diretório base dos resultados (padrão: results)')
    parser.add_argument('--id', required=True, help='Identificador único da execução (ex: tmp01)')
    parser.add_argument('--collection', '-c', default=None, help='Caminho para a coleção Postman (.json) a ser executada')
    parser.add_argument('--environment', '-e', default=None, help='Caminho para o arquivo de ambiente Postman (.postman_environment.json)')
    parser.add_argument('--interactive', action='store_true', help='Modo interativo: verifica dependências e permite instalar o newman se necessário')
    parser.add_argument('--type', default='table', help='Formato(s) de saída: table, csv, plaintext (pode ser múltiplo separado por vírgula)')
    parser.add_argument('--mailjet-api-key', default=None, help='API Key do Mailjet')
    parser.add_argument('--mailjet-api-secret', default=None, help='API Secret do Mailjet')
    parser.add_argument('--send-email-to', default=None, help='Lista de emails de destino, separados por vírgula')
    parser.add_argument('--build-number', default='--', help='Número do build (opcional)')
    parser.add_argument('--commit-hash', default='--', help='Hash do commit (opcional)')
    parser.add_argument('--client-name', default=None, help='Nome do cliente (opcional)')
    args = parser.parse_args()

    id_exec = get_config_value('RUNNER_ID', args.id)
    output_type = get_config_value('RUNNER_TYPE', args.type, 'table')
    collection = get_config_value('RUNNER_COLLECTION', args.collection)
    environment = get_config_value('RUNNER_ENVIRONMENT', args.environment)
    destination = get_config_value('RUNNER_DESTINATION', args.destination)
    mailjet_api_key = get_config_value('MAILJET_API_KEY', args.mailjet_api_key)
    mailjet_api_secret = get_config_value('MAILJET_API_SECRET', args.mailjet_api_secret)
    send_email_to = get_config_value('SEND_EMAIL_TO', args.send_email_to)
    interactive = args.interactive
    build_number = get_config_value('BUILD_NUMBER', args.build_number)
    commit_hash = get_config_value('COMMIT_HASH', args.commit_hash)
    client_name = get_config_value('CLIENT_NAME', args.client_name)

    emails = [e.strip() for e in send_email_to.split(',')] if send_email_to else []

    # Validação obrigatória apenas para id_exec
    if not id_exec:
        print("[ERRO] Parâmetro --id (ou RUNNER_ID) é obrigatório.")
        exit(2)
    return Config(
        id_exec=id_exec,
        output_type=output_type,
        collection=collection,
        environment=environment,
        destination=destination,
        mailjet_api_key=mailjet_api_key,
        mailjet_api_secret=mailjet_api_secret,
        send_email_to=emails,
        interactive=interactive,
        client_name=client_name,
        build_number=build_number,
        commit_hash=commit_hash
    ) 