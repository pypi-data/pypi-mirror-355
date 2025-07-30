from loguru import logger
from pdfplumber.page import Page
from pdfplumber.pdf import PDF
from pdfplumber import open as open_pdf_file
from pathlib import Path
from datetime import datetime
from collections import Counter
from json import dumps
from rapidfuzz.fuzz import partial_ratio, ratio
from rapidfuzz.process import extractOne
from re import compile, IGNORECASE
from FinAnalytics.E.BankStatement.load_extractor import Pipeline, normalize_col
from FinAnalytics.types_used import ExtractorLogs, map_needs, what_we_need, Field, must_have, map_need_literals
from spacy.matcher import Matcher
from spacy.tokens import Doc, Span
from pytz import timezone
from price_parser.parser import CURRENCY_CODES
from tldextract import extract
from typing import Optional
from dateparser.timezone_parser import StaticTzInfo
from geopy.geocoders import Nominatim
from geopy.location import Location
from geopy.extra.rate_limiter import RateLimiter
from timezonefinder import TimezoneFinder
from countryinfo import CountryInfo
from io import BytesIO
# noinspection PyProtectedMember
from price_parser._currencies import CURRENCIES


# from heapq import heappush, heappop


def diff_check(prev_score: float, next_score: float, prev_text: str, next_text: str, compare_to: str):
    p = round(prev_score, 4)
    n = round(next_score, 4)
    # logger.debug("{} - {} is {} and {} - {} is {}", prev_text, compare_to, p, next_text, compare_to, n)
    if p != n:
        return p < n

    # noinspection PyTypeChecker
    result = extractOne(compare_to, (prev_text, next_text), scorer=partial_ratio)
    logger.info(
        "🍹 Fuzz Results: {} b/w {} and {} with {}",
        result, prev_text, next_text, compare_to
    )
    return result[-1] == 1


class ExtractBankStatements:
    logs: ExtractorLogs = {"pages": []}
    pdf_file: PDF

    def __init__(self, source: Path | str | BytesIO, pipeline_path: Optional[str] = None):
        self.pdf_file_path = source
        # please note we expect these words to be already normalized
        self.pipeline = Pipeline(pipeline_path)

        self.all_urls = compile(
            r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})',
            IGNORECASE)
        self.account_id_regex = compile(r'\d+\.?\d*$')

        self.words_we_know = [self.pipeline(_) for _ in what_we_need]

        self.page_index = 0

        self.account_holder_name = ''
        self.timezone: Optional[StaticTzInfo] = None
        self.account_id = ''
        self.bank_name = ''
        self.starting_balance = ''
        self.country_code = ""
        self.currency_used = ''
        self.cached_cols = []
        self.cached_results = {}
        self.reset_logs()
        self.geocoder = RateLimiter(Nominatim(user_agent="FinAnalytics").geocode, min_delay_seconds=1)
        self.tz_finder = TimezoneFinder()
        self.location_details_meta: dict[str, Optional[Location]] = {}
        self.observed_tz: list[str] = []

    def reset_logs(self):
        self.logs["words_we_know"] = what_we_need
        self.logs['bank_name_logs'] = []
        self.logs['bank_url_logs'] = []
        self.logs['account_number_logs'] = []
        self.logs['address_logs'] = []
        self.logs['account_holder_name_logs'] = []

    def __enter__(self):
        self.pdf_file = open_pdf_file(self.pdf_file_path)
        self.logs["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logs["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if self.pdf_file:
            self.pdf_file.close()

    def fetch_urls(self, text: str):
        urls = self.all_urls.findall(text)
        return [_[0] for _ in Counter(
            (extract(url).domain for url in urls if 'bank' in url.lower())
        ).most_common(2)]

    def extract_meta_from_page(self, page_index: int, page_text: str):
        # bank name is the only thing we tend to search in all places if not found else only first page.
        if self.bank_name and self.currency_used:
            return True

        doc = self.pipeline(page_text)

        if not self.account_holder_name:
            self.get_names(doc)

        account_ids: Counter[str] = Counter()
        web_links_for_banks = self.fetch_urls(page_text)
        final_decided_for_bank_name = Field(-1, -1, -1)

        matcher = Matcher(self.pipeline.vocab)

        bank_name_patterns = [
            [
                {"IS_ALPHA": True, "OP": "*", "LENGTH": {">=": 2}},
                {"LOWER": {"REGEX": "^bank$"}}
            ]
        ]
        account_id_patterns = [
            [
                {"LOWER": {"IN": ["account", "a/c", "acc"]}},
                {"LOWER": {"IN": ["no", "number"]}, "OP": "?"},
                {"IS_ASCII": True, "IS_SPACE": False, "OP": "*"},
                {"TEXT": {"REGEX": r"[:\-]?\d{6,}"}}
            ],
            [
                {"TEXT": {"REGEX": r"^a/?c$"}, "LOWER": {"IN": ["a/c", "a", "ac"]}},
                {"LOWER": {"IN": ["no", "number"]}, "OP": "?"},
                {"IS_ASCII": True, "IS_SPACE": False, "OP": "*"},
                {"TEXT": {"REGEX": r"[:\-]?\d{6,}"}}
            ],
        ]
        currency_used_patterns = [
            [
                {"TEXT": {"IN": CURRENCY_CODES}},
            ]
        ]
        address_matcher = [
            [
                {"ENT_TYPE": "GPE", "OP": "+"}
            ],

            # thanks gemini
            [
                {"POS": "PROPN", "OP": "+"},  # "Amrit", "Palam"
                {"IS_DIGIT": True, "OP": "?"},  # "14" in "Sector 14"
                {"LOWER": {
                    "IN": ["vihar", "nagar", "colony", "town", "market", "sector", "phase", "extension", "complex",
                           "enclave", "road", "marg", "street", "lane", "path", "bazar", "chowk", "gali", "avenue",
                           "drive"]}},
                {"IS_ALPHA": True, "OP": "*", "LENGTH": {">=": 2}},
            ],
            # thanks gemini
            [
                {"ENT_TYPE": "GPE", "OP": "+"},  # City (e.g., "Gurugram", "New Delhi")
                {"IS_PUNCT": True, "TEXT": ",", "OP": "?"},  # Optional comma after city
                {"IS_SPACE": True, "OP": "*"},  # Optional space(s)
                {"ENT_TYPE": "GPE", "OP": "+"},  # State/District (e.g., "Haryana", "Delhi")
                {"IS_SPACE": True, "OP": "*"},  # Optional space(s)
                {"TEXT": {"REGEX": r"^\d{6}$"}},  # Mandatory 6-digit PIN code
                {"IS_ALPHA": True, "OP": "*", "LENGTH": {">=": 2}},
            ],
            # thanks gemini
            [
                {"POS": "NUM", "OP": "?"},  # Optional numerical prefix
                {"LOWER": {"IN": ["house", "flat", "door", "no", "block", "sector", "unit"]}},  # Key identifier word
                {"POS": {"IN": ["NUM", "PROPN", "NOUN"]}, "OP": "?"},
                # The number/letter for block/flat (e.g., "A" in "Block A")
                {"TEXT": {"REGEX": r"^[0-9A-Za-z]+$"}, "OP": "?"},  # For apartment numbers like "4B"
                {"IS_PUNCT": True, "OP": "?"},  # Optional dot for "No."
                {"IS_ALPHA": True, "OP": "*", "LENGTH": {">=": 2}},
            ]
        ]

        location_details: dict[str, Location] = {}

        if not self.bank_name:
            matcher.add("BANK_NAME", bank_name_patterns)
        if page_index == 0:
            matcher.add("ACCOUNT_ID", account_id_patterns)
        if not self.timezone or not self.country_code:
            matcher.add('ADDRESS_IN', address_matcher)
        if not self.currency_used:  # there are chances we can find currency in other pages too
            matcher.add("CURRENCY_USED", currency_used_patterns)

        matches = matcher(doc)
        for match_id, start, end in matches:
            token = doc[start:end]
            match self.pipeline.vocab.strings[match_id]:
                case "BANK_NAME":
                    for index, bank in enumerate(web_links_for_banks):
                        # we are using a ratio instead of a partial ratio
                        # to avoid higher scores for just partial matches.
                        score = ratio(token.text.lower(), bank.lower())
                        self.logs['bank_name_logs'].append(f"{token} - {bank} - {score}")
                        if score > .6 and final_decided_for_bank_name.score < score:
                            final_decided_for_bank_name = Field(score, token.text, index)
                case "ACCOUNT_ID":
                    account_ids.update(self.account_id_regex.findall(token.text))
                case "ADDRESS_IN":
                    location_details.update(self.get_location(token))
                case 'CURRENCY_USED':
                    self.currency_used = next(_token.text for _token in token if _token.is_upper)
                    self.logs['currency_used'] = page_index, self.currency_used

        if not self.bank_name and final_decided_for_bank_name.score != -1:
            self.bank_name = final_decided_for_bank_name.matched_with
            self.logs['bank_name'] = page_index, self.bank_name

        if not self.account_id and account_ids:
            self.account_id = account_ids.most_common(1)[0][0]
            self.logs['account_id'] = page_index, self.account_id

        if location_details and not self.timezone:
            timezone_text = Counter(self.observed_tz).most_common(1)[0][0]
            self.timezone = timezone(timezone_text)
            self.logs["timezone"] = self.page_index, timezone_text
            if not (self.currency_used and self.country_code):
                self.get_from_location(location_details[timezone_text])

        if account_ids:
            self.logs['account_number_logs'].append(dict(account_ids))
        if web_links_for_banks:
            self.logs['bank_url_logs'].extend(web_links_for_banks)
        return False

    def get_location(self, token: Span):
        location_details = {}
        for ent in self.pipeline(token.text, warn=False, force_convert=True).ents:
            if ent.label_ not in ('GPE', 'LOC'):
                continue
            location: Optional[Location] = self.geocoder(ent.text, exactly_one=True, language="en", addressdetails=True)
            if not location:
                continue
            self.logs["address_logs"].append(location.raw)
            self.observed_tz.append(self.tz_finder.timezone_at(lng=location.longitude, lat=location.latitude))
            location_details[self.observed_tz[-1]] = location
        return location_details

    def get_from_location(self, location: Location):
        country = location.raw.get("address", {}).get("country", "")
        self.country_code = location.raw.get("address", {}).get("country_code", country)
        self.logs["country_code"] = self.page_index, self.country_code

        if country and not self.currency_used:
            _ = CountryInfo(country).currencies()
            if _:
                self.currency_used = _[0]
                self.logs['currency_used'] = self.page_index, self.currency_used

    def get_names(self, page_doc: Doc):
        names = Counter()

        for ent in page_doc.ents:
            if ent.label_ == "PERSON":
                logger.debug('Identified {} as person name', ent.text)
                names.update([_.strip() for _ in ent.text.split("\n")])

        for row_index, row in enumerate(names):
            for col_index, col in enumerate(names):
                if row_index == col_index:
                    continue
                score = partial_ratio(row.lower(), col.lower())
                if score > 75:
                    selected, replicate = (col, names[row]) \
                        if len(col) > len(row) else (row, names[col])
                    names.update([selected] * replicate)

        if names:
            name, count = names.most_common(1)[0]
            self.account_holder_name = name
            self.logs["account_holder_name_logs"].append(dict(names))
            self.logs["account_holder_name"] = name, count

    def prep(self):
        for page_index, page in enumerate(self.pdf_file.pages):
            self.page_index = page_index
            if self.extract_meta_from_page(page_index, page.extract_text()):
                break

        if self.currency_used and not self.country_code:
            self.country_code = CURRENCIES.get(self.currency_used, {}).get("n", None)

        return all((
            self.account_holder_name, self.account_id,
            self.bank_name, self.currency_used, self.country_code,
            self.timezone
        ))

    def extract_from_pdf(self):
        for page_index, page in enumerate(self.pdf_file.pages):
            self.page_index = page_index
            self.logs["pages"].append({
                "tables_found": [],
                "table_status": [],
                "found_index": -1,
                "page_index": self.page_index,
                "account_holder_name": False
            })
            yield from self.extract_page(page, page_index)

    def extract_page(self, page: Page, page_index: int):
        tables = page.extract_tables()
        page_logs = self.logs["pages"][page_index]
        tables_found = False

        for table_index, table in enumerate(tables):
            if self.cached_cols != table[0]:
                flag, result = self.is_this_transaction_table(table[0])
                page_logs['table_status'].append(flag)
                page_logs['tables_found'].append(dumps(result))

                if not flag:
                    continue

                self.cached_results = result
                self.cached_cols = table[0]
            else:
                result = self.cached_results
                page_logs['table_status'].append(True)
                page_logs['tables_found'].append('cached')

            page_logs["found_index"] = table_index
            tables_found = True

            for row in table[1:]:
                yield {key: row[result[key].match_index] for key in result}

        if not tables_found:
            logger.warning("No table found in page: {}", page_index + 1)

    def pick_best_one(self, compare_to: Doc, compare_from: list[Doc], col_index=0):
        # scores = []
        max_field = Field(-1, '', '')

        for sim_check in compare_from:
            sim_score = self.pipeline.sim_check(compare_to, sim_check)
            logger.debug("🎯 Result for \"{}\" with \"{}\": {}", sim_check, compare_to, sim_score)
            if sim_score < .5:
                continue
            final_score = diff_check(
                max_field.score, sim_score, max_field.matched_with,
                sim_check.text, compare_to.text
            )
            if final_score:
                if max_field.matched_with:
                    logger.debug(
                        "🐳 \"{}\" replaced \"{}\" for match with \"{}\" with tie-score {}", sim_check,
                        max_field.matched_with,
                        compare_to, final_score
                    )

                max_field = Field(
                    score=sim_score, matched_with=sim_check.text, match_index=col_index
                )
                # heappush(scores, max_field)

        return max_field

    def is_this_transaction_table(self, cols: list[str]) -> tuple[bool, dict[map_need_literals, Field]]:
        requirement_mapping: dict[map_need_literals, Field] = {}

        pick_list = [
            self.pick_best_one(self.pipeline(normalize_col(col), force_convert=True), self.words_we_know, col_index)
            for col_index, col in enumerate(cols)
        ]

        for picked in pick_list:
            if picked.matched_with not in map_needs:
                # if no match case like ''
                continue

            if map_needs[picked.matched_with] not in requirement_mapping:
                logger.debug("🥳 Picked {} for {}", cols[picked.match_index], picked.matched_with)
                requirement_mapping[map_needs[picked.matched_with]] = picked
                continue

            prev = requirement_mapping[map_needs[picked.matched_with]]
            if prev.score < picked.score:
                logger.debug(
                    "😄 Picked {} over {} for {}", cols[picked.match_index], cols[prev.match_index],
                    picked.matched_with
                )
                requirement_mapping[map_needs[picked.matched_with]] = picked
                continue

        what_we_found = set(requirement_mapping.keys())
        return must_have.issubset(what_we_found), requirement_mapping
