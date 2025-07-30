import sys
import argparse
from shipyard_email.utils.utils import send_single_email
from shipyard_email.utils import exceptions
import shipyard_bp_utils as shipyard
from shipyard_templates import ShipyardLogger, Messaging, ExitCodeException
import pandas as pd
import os

MAX_SIZE_BYTES = 10000000

logger = ShipyardLogger.get_logger()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-file-name", dest="input_file_name", required=True)
    parser.add_argument(
        "--template-file-name", dest="template_file_name", required=True
    )
    parser.add_argument(
        "--send-method", dest="send_method", default="tls", required=False
    )
    parser.add_argument("--smtp-host", dest="smtp_host", required=True)
    parser.add_argument("--smtp-port", dest="smtp_port", default="", required=True)
    parser.add_argument(
        "--sender-address", dest="sender_address", default="", required=True
    )
    parser.add_argument("--sender-name", dest="sender_name", default="", required=False)
    parser.add_argument("--cc", dest="cc", default="", required=False)
    parser.add_argument("--bcc", dest="bcc", default="", required=False)
    parser.add_argument("--username", dest="username", default="", required=True)
    parser.add_argument("--password", dest="password", default="", required=True)
    parser.add_argument(
        "--include-workflows-footer",
        dest="include_workflows_footer",
        default="TRUE",
        required=False,
    )

    args = parser.parse_args()
    return args


def main():
    try:
        args = get_args()
        sender_address = args.sender_address
        username = args.username or sender_address

        _, input_file_type = os.path.splitext(args.input_file_name)
        _, template_file_type = os.path.splitext(args.template_file_name)

        if input_file_type != ".csv":
            raise exceptions.InvalidFileInputError(
                f"Invalid file type `{args.input_file_name}`. Input file must be '.csv'"
            )

        if template_file_type != ".txt":
            raise exceptions.InvalidFileInputError(
                f"Invalid file type {args.template_file_name}. Template file must be '.txt'"
            )

        if not os.path.exists(args.input_file_name):
            raise exceptions.InvalidFileInputError(
                f"{args.input_file_name} does not exist"
            )

        if not os.path.exists(args.template_file_name):
            raise exceptions.InvalidFileInputError(
                f"{args.template_file_name} does not exist"
            )

        input_table = pd.read_csv(args.input_file_name)
        if len(input_table) == 0:
            pass

        template = ""
        with open(args.template_file_name, "r", encoding="utf-8") as file:
            template = file.read()

        for index, row in input_table.iterrows():
            message = template
            for col_name in input_table.columns:
                message = message.replace(f"{{{{{col_name}}}}}", str(row[col_name]))
            send_single_email(
                send_method=args.send_method,
                sender_address=sender_address,
                username=username,
                message=message,
                include_workflows_footer=shipyard.args.convert_to_boolean(
                    args.include_workflows_footer, default=True
                ),
                smtp_host=args.smtp_host,
                smtp_port=args.smtp_port,
                password=args.password,
                sender_name=args.sender_name,
                to=str(row["email"]),
                cc=args.cc,
                bcc=args.bcc,
                subject=str(row["subject"]),
                inject_file_content=False,
            )

    except ExitCodeException as error:
        logger.error(error.message)
        sys.exit(error.exit_code)
    except Exception as e:
        logger.error(f"Failed to send email. {e}")
        sys.exit(Messaging.EXIT_CODE_UNKNOWN_ERROR)


if __name__ == "__main__":
    main()
