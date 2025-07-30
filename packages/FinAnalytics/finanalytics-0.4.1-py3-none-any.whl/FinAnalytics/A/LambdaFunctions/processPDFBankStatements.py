from FinAnalytics.E.BankStatement.extract_pdf import ExtractBankStatements
from FinAnalytics.T.BankStatements.understandExchanges import PrepBankStatement
from FinAnalytics.A.DB.LoadRecords import LoadRecords
from FinAnalytics.types_used import FinalProcessFileLogs
from loguru import logger
from sys import stdout
from boto3 import client
from io import BytesIO
from contextlib import closing
from json import dumps
from aws_lambda_typing.events import S3Event

# make sure to load dot env at your side.

logger.remove(0)
logger.add(stdout, level="INFO")


def main(event: S3Event, pipeline_path: str = None):
    with closing(client('s3')) as s3:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        response = s3.get_object(Bucket=bucket, Key=key)
        with ExtractBankStatements(BytesIO(response["Body"].read()), pipeline_path) as pdf:
            status = pdf.prep()
            if not status:
                final_logs: FinalProcessFileLogs = {
                    'extractor_logs': pdf.logs,
                    'transport_logs': None
                }
                logger.error("Failed to extract basic info. from the Bank Statement.")
                return {
                    'statusCode': 500,
                    'body': dumps({"processed": True, "logs": final_logs})
                }

            t = PrepBankStatement(
                "PDF", key,
                pdf.currency_used, pdf.bank_name,
                pdf.account_holder_name, pdf.account_id,
                pdf.country_code, pdf.timezone
            )
            with LoadRecords() as transporter:
                for record in pdf.extract_from_pdf():
                    p = t.process_record(record)
                    if not p:
                        continue
                    transporter.push(t.process_record(record))

            final_logs: FinalProcessFileLogs = {
                'extractor_logs': pdf.logs,
                'transport_logs': transporter.logs
            }

        return {
            'statusCode': 200,
            'body': dumps({"processed": True, "logs": final_logs})
        }
