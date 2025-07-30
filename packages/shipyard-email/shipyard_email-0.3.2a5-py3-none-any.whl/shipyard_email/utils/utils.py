import shipyard_bp_utils as shipyard
from shipyard_email.email_client import EmailClient
from shipyard_templates import ShipyardLogger

MAX_SIZE_BYTES = 10000000

logger = ShipyardLogger.get_logger()


def send_single_email(
    send_method: str,
    sender_address: str,
    username: str,
    message: str,
    include_workflows_footer: bool,
    smtp_host: str,
    smtp_port: int,
    password: str,
    sender_name: str,
    to: str,
    cc: str,
    bcc: str,
    subject: str,
    inject_file_content: bool = True,
):
    send_method = send_method.lower() or "tls"
    sender_address = sender_address
    username = username
    message = message

    client = EmailClient(smtp_host, smtp_port, username, password, send_method)

    client.send_message(
        sender_address=sender_address,
        message=message,
        sender_name=sender_name,
        to=to,
        cc=cc,
        bcc=bcc,
        subject=subject,
        include_footer=include_workflows_footer,
        inject_files=inject_file_content,
    )
