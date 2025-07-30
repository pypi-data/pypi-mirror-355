# -*- coding: utf-8 -*-
from collections import namedtuple
from typing import TypedDict, List, Dict, Union, Literal, Tuple, Optional

Field = namedtuple("Score", ["score", "matched_with", "match_index"])
Source = Literal["API", "PDF"]


class DBField(TypedDict):
    ID: int
    Reference: str
    AccountHolderName: str
    AccountID: str
    CurrencyUsed: str
    BankName: str
    Credit: float
    Debit: float
    Balance: float
    Description: str
    Timestamp: float


what_we_need = [
    'id', 'cheque number',
    'transaction time', 'transaction start time', 'timestamp', 'time',
    'debit',
    'credit',
    'description', 'message', 'details',
    'balance'
]

map_need_literals = Literal["ID", "Timestamp", "Debit", "Credit", "Desc", "Balance"]
meta_info = Literal["AccountHolderName", "AccountNumber", "CurrencyUsed", "BankName"]

map_needs: Dict[str, map_need_literals] = {
    "id": "ID", "cheque number": "ID",

    "timestamp": "Timestamp", "transaction time": "Timestamp",
    "transaction start time": "Timestamp", "time": "Timestamp",

    "debit": "Debit",

    "credit": "Credit",

    "description": "Desc", "message": "Desc", "details": "Desc",

    "balance": "Balance"
}

must_have = {"Balance", "Timestamp"}
must_but_can_optional = {"Debit", "Credit"}
model_name = "en_core_web_md_with_custom_vectors"


class LogForPdfPages(TypedDict):
    tables_found: List[str]
    table_status: List[bool]
    found_index: int
    page_index: int
    account_holder_name: Union[bool, str]


class ExtractorLogs(TypedDict):
    words_we_know: List[str]
    start_time: str
    end_time: str
    has_unknown_vectors: bool
    pages: List[LogForPdfPages]
    account_holder_name: Tuple[str, int]
    country_code: Tuple[int, str]
    account_id: Tuple[int, str]
    bank_name: Tuple[int, str]
    currency_used: Tuple[int, str]
    starting_amount: Tuple[int, str]
    starting_balance: Tuple[int, str]
    timezone: Tuple[int, str]
    account_number_logs: List[Dict[str, int]]
    account_holder_name_logs: List[Dict[str, int]]
    address_logs: List[Dict]
    bank_name_logs: List[str]
    bank_url_logs: List[str]


class PutTransportLog(TypedDict):
    page_index: Optional[int]
    resp: Dict


class TransporterLogs(TypedDict):
    put_logs: List[PutTransportLog]


class FinalProcessFileLogs(TypedDict):
    extractor_logs: ExtractorLogs
    transport_logs: Optional[TransporterLogs]
