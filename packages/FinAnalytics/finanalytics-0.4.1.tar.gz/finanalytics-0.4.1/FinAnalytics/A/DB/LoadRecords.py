from boto3 import client
from FinAnalytics.A.DB.constants import TRANSACTIONS_TABLE_NAME
from os import getenv
from FinAnalytics.types_used import TransporterLogs, PutTransportLog
from typing import Dict, Optional


class LoadRecords:
    def __init__(self):
        self.batch_put = []
        self.client = client('dynamodb', endpoint_url=getenv('ENDPOINT_URL'))
        self.reference_pt: Optional[int] = None
        self.logs: TransporterLogs = {"put_logs": []}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self.clear_batch()
        self.client.close()

    def clear_batch(self):
        if not self.batch_put:
            return

        resp: Dict = self.client.batch_write_item(
            RequestItems={
                TRANSACTIONS_TABLE_NAME: list(map(
                    lambda item: dict(PutRequest=dict(Item=item)),
                    self.batch_put
                ))
            }
        )
        put_log: PutTransportLog = dict(page_index=self.reference_pt, resp=resp)
        self.logs['put_logs'].append(put_log)
        self.batch_put.clear()

    def push(self, row):
        if len(self.batch_put) == 20:
            self.clear_batch()
        self.batch_put.append(row)
