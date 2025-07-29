import logging
from pathlib import Path
from typing import List, Optional
import requests

def send_email_report(
    mailjet_api_key: str,
    mailjet_api_secret: str,
    recipients: List[str],
    html_report_path: Path,
    sender_email: str = "no-reply@ucloud.services",
    sender_name: str = "UCloud | Newman Runner",
    client_name: Optional[str] = None,
    id: Optional[str] = None
) -> bool:
    """Envia o relatório HTML gerado pelo Newman por email via Mailjet para todos os destinatários.

    Args:
        mailjet_api_key: Credencial da API Key do Mailjet.
        mailjet_api_secret: Credencial da API Secret do Mailjet.
        recipients: Lista de emails de destino.
        html_report_path: Caminho do arquivo HTML gerado pelo Newman.
        sender_email: Email do remetente.
        sender_name: Nome do remetente.
        client_name: Nome do cliente (opcional).

    Returns:
        bool: True se o email foi enviado com sucesso, False caso contrário.
    """
    if not mailjet_api_key or not mailjet_api_secret:
        logging.warning("Mailjet API Key/Secret não configurados. Email não será enviado.")
        return False
    if not recipients:
        logging.warning("Nenhum destinatário informado. Email não será enviado.")
        return False
    if not html_report_path or not Path(html_report_path).exists():
        logging.error(f"Arquivo HTML do relatório não encontrado: {html_report_path}")
        return False
    try:
        with open(html_report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        logging.error(f"Erro ao ler HTML para email: {e}")
        return False
    url = "https://api.mailjet.com/v3.1/send"
    auth = (mailjet_api_key, mailjet_api_secret)
    to_list = [{"Email": email, "Name": email.split('@')[0]} for email in recipients]
    subject = f"UCloud | Newman Runner | Relatório de Testes"
    client_name = f"{client_name} # {id}"
    subject = f"UCloud | Newman Runner | [{client_name}] Relatório de Testes"
    data = {
        "Messages": [
            {
                "From": {"Email": sender_email, "Name": sender_name},
                "To": to_list,
                "Subject": subject,
                "HTMLPart": html_content
            }
        ]
    }
    try:
        response = requests.post(url, auth=auth, json=data)
        response.raise_for_status()
        logging.info(f"✅ Email enviado com sucesso para: {', '.join(recipients)}")
        return True
    except Exception as e:
        logging.error(f"❌ Erro ao enviar email: {e}")
        return False 