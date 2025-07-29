import csv
from pathlib import Path
from typing import List, Dict, Any

def write_csv_report(results: List[Dict[str, Any]], csv_path: Path) -> None:
    """Gera um relatório CSV resumido das coleções executadas.

    Args:
        results: Lista de dicionários com resultados das execuções.
        csv_path: Caminho do arquivo CSV de saída.
    """
    fieldnames = [
        'collection', 'status', 'total_requests', 'failed_requests',
        'total_assertions', 'failed_assertions', 'success_rate', 'assertion_success_rate',
        'html_report', 'json_report'
    ]
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            m = r['metrics']
            writer.writerow({
                'collection': r['collection'],
                'status': r['status'],
                'total_requests': m.get('total_requests', 0),
                'failed_requests': m.get('failed_requests', 0),
                'total_assertions': m.get('total_assertions', 0),
                'failed_assertions': m.get('failed_assertions', 0),
                'success_rate': m.get('success_rate', 0),
                'assertion_success_rate': m.get('assertion_success_rate', 0),
                'html_report': r['html_report'],
                'json_report': r['json_report'],
            })

def write_plaintext_table(results: List[Dict[str, Any]], txt_path: Path) -> None:
    """Gera um relatório em texto plano (tabela alinhada) das coleções executadas.

    Args:
        results: Lista de dicionários com resultados das execuções.
        txt_path: Caminho do arquivo TXT de saída.
    """
    headers = [
        'Collection', 'Status', 'Total Req', 'Failed Req',
        'Total Assert', 'Failed Assert', 'Req %', 'Assert %'
    ]
    lines = []
    lines.append(' | '.join(f"{h:>14}" for h in headers))
    lines.append('-' * (len(headers) * 16))
    for r in results:
        m = r['metrics']
        row = [
            r['collection'],
            r['status'],
            str(m.get('total_requests', 0)),
            str(m.get('failed_requests', 0)),
            str(m.get('total_assertions', 0)),
            str(m.get('failed_assertions', 0)),
            f"{m.get('success_rate', 0):.1f}%",
            f"{m.get('assertion_success_rate', 0):.1f}%"
        ]
        lines.append(' | '.join(f"{v:>14}" for v in row))
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n') 