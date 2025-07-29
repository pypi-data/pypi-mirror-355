#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import json
import subprocess
import logging
import argparse
import shutil
import sys
from pathlib import Path
from typing import Dict, Any
from runner.emailer import send_email_report
from runner.reporting import write_csv_report, write_plaintext_table
from runner.config import Config
import time
from jinja2 import Environment, PackageLoader, select_autoescape

def ensure_directories(config: Config) -> None:
    """Garante que todos os diretórios necessários existem.

    Args:
        config: Objeto de configuração.
    """
    for d in [config.artifacts_html_dir, config.artifacts_json_dir, config.artifacts_dir, config.logs_dir]:
        d.mkdir(parents=True, exist_ok=True)


def process_newman_results(json_report: str) -> Dict[str, Any]:
    """Processa os resultados do Newman para extrair métricas importantes.

    Args:
        json_report: Caminho do arquivo JSON de saída do Newman.

    Returns:
        Dicionário com métricas extraídas.
    """
    try:
        with open(json_report, 'r') as f:
            data = json.load(f)
        total_requests = len(data.get('run', {}).get('executions', []))
        failed_requests = 0
        total_assertions = 0
        failed_assertions = 0
        for exec in data.get('run', {}).get('executions', []):
            assertions = exec.get('assertions', [])
            total_assertions += len(assertions)
            failed_assertions += sum(1 for a in assertions if not a.get('passed', True))
            if assertions:
                if any(not a.get('passed', True) for a in assertions):
                    failed_requests += 1
            else:
                # Se não há assertions, considere falha apenas se status >= 400
                if exec.get('response', {}).get('code', 200) >= 400:
                    failed_requests += 1
        return {
            'total_requests': total_requests,
            'failed_requests': failed_requests,
            'total_assertions': total_assertions,
            'failed_assertions': failed_assertions,
            'success_rate': ((total_requests - failed_requests) / total_requests) * 100 if total_requests > 0 else 0,
            'assertion_success_rate': ((total_assertions - failed_assertions) / total_assertions) * 100 if total_assertions > 0 else 0
        }
    except Exception as e:
        logging.error(f"❌ Erro ao processar resultados do Newman: {str(e)}")
        return {}


def check_newman_interactive() -> bool:
    """Verifica se o newman está disponível. Se não, pergunta se deseja instalar.

    Returns:
        bool: True se o newman está disponível ou foi instalado, False caso contrário.
    """
    if shutil.which('newman') is not None:
        return True
    print("\n🚩 O comando 'newman' não foi localizado no seu PATH.")
    print("💡 Dica: O Newman é essencial para executar os testes automatizados. Vamos instalar juntos?")
    resp = input("Deseja instalar o newman globalmente via 'npm install -g newman'? [s/N]: ").strip().lower()
    if resp == 's':
        try:
            subprocess.check_call(['npm', 'install', '-g', 'newman'])
            print("✅ Newman instalado com sucesso! Pronto para acelerar seus testes 🚀\n")
            return shutil.which('newman') is not None
        except Exception as e:
            logging.error(f"⚠️ Não foi possível instalar o Newman automaticamente. Por favor, tente instalar manualmente. Detalhes: {e}")
            return False
    else:
        logging.warning("Execução pausada. Instale o Newman manualmente e execute novamente para continuar sua jornada de automação!")
        return False


def run_newman(config: Config) -> bool:
    """Executa os testes Newman e gera relatórios.

    Args:
        config: Objeto de configuração.

    Returns:
        bool: True se todos os testes passaram, False caso contrário.
    """
    try:
        if config.collection:
            collection_paths = [Path(p.strip()) for p in config.collection.split(',')]
            colecoes_nao_encontradas = [str(p) for p in collection_paths if not p.exists()]
            if colecoes_nao_encontradas:
                logging.error(f"🔎 Atenção: Não localizamos a(s) coleção(ões): {', '.join(colecoes_nao_encontradas)}. Verifique o caminho e tente novamente. Estamos aqui para ajudar!")
                return False
            collections = collection_paths
        else:
            collections = list(Path('/app').glob('*.postman_collection.json'))
        if not collections:
            logging.error("📂 Nenhuma coleção Postman foi encontrada. Adicione sua coleção e potencialize seus testes!")
            return False
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results = []
        total_metrics = {
            'total_requests': 0,
            'failed_requests': 0,
            'total_assertions': 0,
            'failed_assertions': 0
        }
        for collection in collections:
            msg_ambiente = "[N/A]"
            if config.environment:
                msg_ambiente = Path(config.environment).name
            html_report = str(config.artifacts_html_dir / f"{collection.stem}_{timestamp}.html")
            json_report = str(config.artifacts_json_dir / f"{collection.stem}_{timestamp}.json")
            cmd = [
                'newman', 'run', str(collection),
                '--reporters', 'cli,json',
                '--reporter-json-export', json_report,
                '--suppress-exit-code'
            ]
            if config.environment:
                cmd.extend(['--environment', str(config.environment)])
            start_time = time.time()
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            with open(config.log_file, 'a', encoding='utf-8') as flog:
                flog.write(f"\n\n[INÍCIO DE EXECUÇÃO] {datetime.now().isoformat()} - {collection.name}\n")
                for line in process.stdout:
                    print(line, end='')  # Console em tempo real
                    flog.write(line)    # Arquivo de log em tempo real
            process.wait()
            total_elapsed = time.time() - start_time
            metrics = process_newman_results(json_report)
            total_metrics['total_requests'] += metrics.get('total_requests', 0)
            total_metrics['failed_requests'] += metrics.get('failed_requests', 0)
            total_metrics['total_assertions'] += metrics.get('total_assertions', 0)
            total_metrics['failed_assertions'] += metrics.get('failed_assertions', 0)
            print_summary(collection.name, msg_ambiente, metrics, html_report, json_report, total_elapsed)
            logging.info(f"📜 Log completo disponível em: {config.log_file.resolve()} (transparência total para seu time)")
            test_result = {
                'collection': collection.name,
                'status': 'SUCCESS' if process.returncode == 0 else 'FAILURE',
                'html_report': html_report,
                'json_report': json_report,
                'metrics': metrics
            }
            results.append(test_result)
            if process.returncode == 0:
                logging.info(f"✅ {collection.name}: Testes concluídos com sucesso! Compartilhe o resultado e inspire seu time! 🚀")
            else:
                logging.warning(f"⚠️ {collection.name}: Alguns testes falharam. Use os relatórios para identificar oportunidades de melhoria!")
            # Geração do HTML customizado via Jinja2
            try:
                render_jinja2_html(json_report, html_report, timestamp=timestamp)
                logging.info(f"[JINJA2] Relatório HTML customizado gerado em: {html_report}")
            except Exception as e:
                logging.error(f"[JINJA2] Erro ao gerar HTML customizado: {e}")
                logging.error(f"[JINJA2] Traceback: {e.__traceback__}")
        total_metrics['overall_success_rate'] = (
            (total_metrics['total_requests'] - total_metrics['failed_requests']) /
            total_metrics['total_requests'] * 100 if total_metrics['total_requests'] > 0 else 0
        )
        total_metrics['assertion_success_rate'] = (
            (total_metrics['total_assertions'] - total_metrics['failed_assertions']) /
            total_metrics['total_assertions'] * 100 if total_metrics['total_assertions'] > 0 else 0
        )
        summary = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'total_metrics': total_metrics,
            'environment': msg_ambiente,
            'build_number': config.build_number,
            'commit_hash': config.commit_hash
        }
        with open(config.artifacts_dir / 'output.json', 'w') as f:
            json.dump(summary, f, indent=2)
        # Após salvar o summary JSON, gerar CSV e plaintext se solicitado
        output_types = [t.strip() for t in config.output_type.split(',')]
        if 'csv' in output_types:
            csv_dir = config.artifacts_dir / 'csv'
            csv_dir.mkdir(parents=True, exist_ok=True)
            write_csv_report(results, csv_dir / 'output.csv')
        if 'plaintext' in output_types or 'table' in output_types:
            txt_dir = config.artifacts_dir / 'text'
            txt_dir.mkdir(parents=True, exist_ok=True)
            write_plaintext_table(results, txt_dir / 'output.txt')
        return all(r['status'] == 'SUCCESS' for r in results)
    except Exception as e:
        logging.error(f"🚨 Ocorreu um erro inesperado ao executar os testes Newman. Detalhes: {str(e)}. Não desanime, revise o erro e conte conosco para evoluir!")
        return False

def print_summary(collection_name: str, environment: str, metrics: Dict[str, Any], html_report: str, json_report: str, elapsed: float) -> None:
    """Imprime o resumo da execução de uma coleção com UX/UI e growth hacking."""
    # Cores ANSI
    BOLD = '\033[1m'
    RESET = '\033[0m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    SEPARATOR = f"{CYAN}{'━'*56}{RESET}"

    print(f"\n{SEPARATOR}")
    print(f"🌐 {BOLD}Coleção:{RESET} {collection_name}")
    print(f"🌐 {BOLD}Ambiente:{RESET} {environment}")
    print(f"{SEPARATOR}")
    print(f"⏳ {YELLOW}Execução em andamento...{RESET}")
    print(f"\n⏱️  {BOLD}Tempo total de execução:{RESET} {elapsed:.2f}s\n")
    print(f"{GREEN if metrics.get('failed_requests', 0) == 0 and metrics.get('failed_assertions', 0) == 0 else RED}📊 {BOLD}Métricas de Qualidade:{RESET}")
    print(f"   • Total de requisições:      {BOLD}{metrics.get('total_requests', 0)}{RESET}")
    print(f"   • Requisições com falha:     {RED if metrics.get('failed_requests', 0) else GREEN}{metrics.get('failed_requests', 0)}{RESET}")
    print(f"   • Total de assertions:       {BOLD}{metrics.get('total_assertions', 0)}{RESET}")
    print(f"   • Assertions com falha:      {RED if metrics.get('failed_assertions', 0) else GREEN}{metrics.get('failed_assertions', 0)}{RESET}")
    print(f"   • Sucesso em requests:       {BOLD}{metrics.get('success_rate', 0):.1f}%{RESET}")
    print(f"   • Sucesso em assertions:     {BOLD}{metrics.get('assertion_success_rate', 0):.1f}%{RESET}")
    print(f"\n{BLUE}📁 {BOLD}Relatórios Gerados:{RESET}")
    print(f"   • HTML: {html_report}")
    print(f"   • JSON: {json_report}")
    print(f"\n{SEPARATOR}")
    if metrics.get('failed_requests', 0) == 0 and metrics.get('failed_assertions', 0) == 0:
        print(f"{GREEN}🎉 Sucesso total! Todos os testes passaram. Compartilhe este resultado e inspire seu time a ir além! 🚀{RESET}")
    else:
        print(f"{YELLOW}⚠️ Alguns testes não passaram. Veja os relatórios, aprenda com os resultados e evolua continuamente!{RESET}")
    print(f"{CYAN}💡 Dica de crescimento: Use os relatórios HTML para identificar oportunidades de melhoria e celebrar conquistas!{RESET}\n")

def check_dependency(cmd, name, min_version=None):
    try:
        result = subprocess.run([cmd, '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip().split('\n')[0]
            print(f"[OK] {name}: {version}")
            if min_version and min_version not in version:
                print(f"[WARN] {name}: versão recomendada é {min_version}")
            return True
        else:
            print(f"[ERRO] {name} não encontrado ou erro ao executar.")
            return False
    except FileNotFoundError:
        print(f"[ERRO] {name} não encontrado no PATH.")
        return False

def install_dependency(name):
    print(f"\n🔧 Instalando {name}...")
    if name == 'Node.js':
        subprocess.run(['curl', '-fsSL', 'https://deb.nodesource.com/setup_18.x', '|', 'bash', '-'], check=True)
        subprocess.run(['apt-get', 'install', '-y', 'nodejs'], check=True)
        return
    if name == 'npm':
        print("O npm é instalado junto com o Node.js.")
        return
    if name == 'pnpm':
        subprocess.run(['npm', 'install', '-g', 'pnpm'], check=True)
        return
    if name == 'Newman':
        subprocess.run(['npm', 'install', '-g', 'newman'], check=True)
        return
    print(f"[ERRO] Instalação automática não implementada para {name}.")

def validate_environment(auto_install=False):
    print("\n🔎 Validando premissas do ambiente:\n")
    missing = []
    ok = True
    if not check_dependency('node', 'Node.js', '18.12'):
        missing.append('Node.js')
        ok = False
    if not check_dependency('npm', 'npm'):
        missing.append('npm')
        ok = False
    if not check_dependency('pnpm', 'pnpm'):
        missing.append('pnpm')
        ok = False
    if not check_dependency('newman', 'Newman'):
        missing.append('Newman')
        ok = False
    if not check_dependency('python3', 'Python 3'):
        missing.append('Python 3')
        ok = False
    if ok:
        print("\n✅ Ambiente pronto! Tudo certo para turbinar sua automação com o ucloud-newman-runner!")
        sys.exit(0)
    else:
        print(f"\n🔎 Ambiente com pendências: {', '.join(missing)}")
        if auto_install:
            for dep in missing:
                install_dependency(dep)
            print("\n✅ Dependências instaladas! Execute novamente a validação para garantir que tudo está perfeito.")
            sys.exit(0)
        else:
            resp = input("Deseja instalar as dependências ausentes agora? (S/n): ").strip().lower()
            if resp in ('s', 'sim', ''):
                for dep in missing:
                    install_dependency(dep)
                print("\n✅ Dependências instaladas! Execute novamente a validação para garantir que tudo está perfeito.")
                sys.exit(0)
            else:
                print("Execução finalizada sem instalar dependências. Quando quiser, estamos prontos para ajudar!")
                sys.exit(1)

def render_jinja2_html(json_path, html_path, timestamp=None):
    """Gera o HTML a partir do JSON do Newman usando o template Jinja2."""
    from pathlib import Path
    import json
    import types
    import logging
    template_dir = Path(__file__).parent.parent.parent / 'templates'
    template_file = 'report_template.html.j2'
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    if timestamp:
        data['timestamp'] = timestamp
    # Robustez: garantir tipos corretos para o template
    def fix_field(obj, key, default):
        val = obj.get(key, default)
        if isinstance(val, (types.BuiltinFunctionType, types.FunctionType, types.MethodType)):
            obj[key] = default
        elif key not in obj or not isinstance(val, type(default)):
            obj[key] = default
    if 'run' in data:
        fix_field(data['run'], 'executions', [])
        fix_field(data['run'], 'failures', [])
        fix_field(data['run'], 'stats', {})
        fix_field(data['run'], 'timings', {})
    if 'environment' in data:
        fix_field(data['environment'], 'values', [])
    # # Loga os valores reais para debug
    # def log_verbose(path, value):
    #     logging.error(f"[JINJA2-DEBUG] {path}: {type(value)} -> {repr(value)[:300]}")
    # log_verbose('run.executions', data.get('run', {}).get('executions'))
    # log_verbose('run.failures', data.get('run', {}).get('failures'))
    # log_verbose('run.stats', data.get('run', {}).get('stats'))
    # log_verbose('run.timings', data.get('run', {}).get('timings'))
    # log_verbose('environment.values', data.get('environment', {}).get('values'))
    # Debug avançado: checa se algum campo é função/método
    # def check_for_functions(obj, prefix=''):
    #     if isinstance(obj, dict):
    #         for k, v in obj.items():
    #             if isinstance(v, (types.BuiltinFunctionType, types.FunctionType, types.MethodType)):
    #                 logging.error(f"[JINJA2-ERROR] Campo problemático: {prefix + k} = {v} ({type(v)})")
    #                 raise RuntimeError(f"Campo problemático: {prefix + k} = {v} ({type(v)})")
    #             if isinstance(v, dict):
    #                 check_for_functions(v, prefix + k + '.')
    #             if isinstance(v, list):
    #                 for i, item in enumerate(v):
    #                     if isinstance(item, (types.BuiltinFunctionType, types.FunctionType, types.MethodType)):
    #                         logging.error(f"[JINJA2-ERROR] Campo problemático: {prefix + k}[{i}] = {item} ({type(item)})")
    #                         raise RuntimeError(f"Campo problemático: {prefix + k}[{i}] = {item} ({type(item)})")
    #                     if isinstance(item, dict):
    #                         check_for_functions(item, prefix + k + f'[{i}].')
    # check_for_functions(data)
    
    env = Environment(
        loader=PackageLoader("runner", "templates"),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template(template_file)
    html = template.render(**data)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

def main():
    parser = argparse.ArgumentParser(description="Runner de testes Newman UCloud")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run', action='store_true', help='Executa o runner de testes')
    group.add_argument('--validate', action='store_true', help='Valida premissas do ambiente (Node, Newman, etc)')
    parser.add_argument('--install', action='store_true', help='(com --validate) Instala automaticamente as dependências ausentes')
    parser.add_argument('--destination', '-d', default='results', help='Diretório base dos resultados (padrão: results)')
    parser.add_argument('--id', help='Identificador único da execução (ex: tmp01)')
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

    if args.validate:
        validate_environment(auto_install=args.install)
    elif args.run:
        if not args.id:
            from datetime import datetime
            args.id = datetime.now().strftime('%Y%m%d%H%M%S')
            print(f"[INFO] Nenhum --id fornecido. Gerando id automaticamente: {args.id}")
        emails = [e.strip() for e in (args.send_email_to or '').split(',')] if args.send_email_to else []
        config = Config(
            id_exec=args.id,
            output_type=args.type,
            collection=args.collection,
            environment=args.environment,
            destination=args.destination,
            mailjet_api_key=args.mailjet_api_key,
            mailjet_api_secret=args.mailjet_api_secret,
            send_email_to=emails,
            interactive=args.interactive,
            client_name=args.client_name,
            build_number=args.build_number,
            commit_hash=args.commit_hash
        )
        print(f"[RUN] Execução do runner iniciada para id={config.id_exec}")

        # Setup de logging (arquivo + console)
        config.logs_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        # Criação dos diretórios necessários
        ensure_directories(config)

        # Execução do Newman
        success = run_newman(config)

        # Envio de e-mail se configurado
        if config.mailjet_api_key and config.mailjet_api_secret and config.send_email_to:
            # Localiza o HTML gerado da primeira coleção (padrão)
            html_report_path = None
            if hasattr(config, 'artifacts_html_dir') and config.artifacts_html_dir.exists():
                htmls = list(config.artifacts_html_dir.glob('*.html'))
                if htmls:
                    html_report_path = htmls[0]
            if not html_report_path:
                logging.error("[EMAIL] Relatório HTML não encontrado para envio.")
            else:
                try:
                    send_ok = send_email_report(
                        config.mailjet_api_key,
                        config.mailjet_api_secret,
                        config.send_email_to,
                        html_report_path,
                        client_name=config.client_name,
                        id=config.id_exec
                    )
                    if not send_ok:
                        logging.warning("[EMAIL] Não foi possível enviar o relatório por e-mail desta vez. Revise as configurações e tente novamente. Estamos juntos nessa!")
                except Exception as e:
                    logging.error(f"[EMAIL] Ocorreu um erro ao enviar o e-mail: {e}. Não se preocupe, revise as configurações e tente novamente!")
        else:
            logging.info("[EMAIL] Envio de e-mail não configurado ou destinatários ausentes. Configure para compartilhar resultados e engajar seu time!")

        # Código de saída apropriado
        if success:
            logging.info("✅ Execução concluída com sucesso! Parabéns por mais um passo rumo à excelência em automação! 🚀")
            sys.exit(0)
        else:
            logging.error("⚠️ Execução concluída com falhas. Use os relatórios para aprender, evoluir e alcançar resultados ainda melhores na próxima rodada!")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 