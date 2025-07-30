from os import getenv
import boto3
from dotenv import load_dotenv
from contextlib import closing
from FinAnalytics.A.DB.constants import TRANSACTIONS_TABLE_NAME


def main():
    with closing(boto3.client('dynamodb', endpoint_url=getenv('ENDPOINT_URL'))) as dynamodb:
        resp = dynamodb.update_table(
            TableName=TRANSACTIONS_TABLE_NAME,
            DeletionProtectionEnabled=False,
        )
        print(resp)


if __name__ == "__main__":
    load_dotenv()
    main()
