from pandas import DataFrame
from dateparser.timezone_parser import StaticTzInfo
from dateparser.utils import apply_timezone
from FinAnalytics.types_used import map_need_literals, Source
from price_parser import parse_price
from dateparser import parse
from typing import Optional
from hashlib import sha256


def get_hash_brown(desc: str, timestamp: str):
    return str(sha256(str.encode(timestamp + desc)).hexdigest())[: 16]


class PrepBankStatement:
    frame: DataFrame
    logs = {}

    def __init__(
            self,
            source: Source, source_grp: str,
            currency_used: str, bank_name: str, account_holder_name: str, account_id: str, country_code: str,
            timezone: Optional[StaticTzInfo] = None
    ):
        self.source = source
        self.source_grp = source_grp
        self.currency_used = currency_used
        self.bank_name = bank_name
        self.account_holder_name = account_holder_name
        self.account_id = account_id
        self.timezone = timezone
        self.country_code = country_code

    def convert_amount(self, number: str) -> float:
        comma_s = number.count(",")
        has_comma = comma_s > 0
        sep = '.'

        if has_comma > 1:
            sep = ','

        return parse_price(
            number, currency_hint=self.currency_used,
            decimal_separator=sep
        ).amount_float or 0

    def parse_stamp(self, time_stamp: str):
        result = parse(time_stamp, region=self.country_code, settings=None if self.country_code else dict(DATE_ORDER="DMY"))
        if not result:
            return False

        if self.timezone:
            result.replace(tzinfo=self.timezone)

        return result

    def process_record(self, record: dict[map_need_literals, str]):
        date_obj = self.parse_stamp(record["Timestamp"])
        if not date_obj:
            return False

        time_stamp = date_obj.timestamp()
        date_string = date_obj.strftime("%d-%m-%Y")

        debit_value = self.convert_amount(record['Debit'])
        return {
            "Date": {
                'S': date_string
            },
            "Source": {
                'S': self.source
            },
            "SourceGrp": {
                'S': self.source_grp
            },
            "ID": {
                'S': get_hash_brown(record['Desc'], str(time_stamp))
            },
            "Reference": {
                'S': record['ID']
            },
            "BankName": {
                'S': self.bank_name
            },
            "AccountHolderName": {
                'S': self.account_holder_name
            },
            "AccountID": {
                'S': self.account_id
            },
            "CurrencyUsed": {
                'S': self.currency_used
            },
            "Description": {
                'S': record['Desc']
            },
            "Credit": {
                'N': str(self.convert_amount(record['Credit']))
            },
            "Debit": {
                'N': str(debit_value)
            },
            "IsDebit": {
                'BOOL': debit_value > 0
            },
            "Balance": {
                'N': str(self.convert_amount(record['Balance']))
            },
            "Timestamp": {
                'N': str(time_stamp)
            },
            "IsProcessed": {
                'N': "0"
            },
        }
