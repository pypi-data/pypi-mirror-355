from spacy import load
from pathlib import Path
from typing import Union, Optional
from loguru import logger
from spacy.tokens import Doc
from rapidfuzz.fuzz import partial_ratio
from FinAnalytics.types_used import model_name


def normalize_col(col):
    col = col.lower().strip()
    col = col.replace("_", " ").replace(".", "")
    return col


class Pipeline:
    def __init__(self, path: Optional[Union[str, Path]] = None):
        priority = [path, Path.cwd(), Path(__file__).parent]
        for _ in priority:
            if not (_ and (_ / model_name).exists()):
                continue
            self.pipeline = load(_ / model_name)
            break

    @property
    def vocab(self):
        return self.pipeline.vocab

    def __call__(self, text: str, warn: bool = True, force_convert: bool = False):
        result = self.pipeline(normalize_col(text) if force_convert else text)
        if warn and not result.has_vector:
            logger.warning("The word: \"{}\"(\"{}\") has no vector, please train the model accordingly", result, text)
        return result

    def sim_check(self, first_doc: Doc, second_doc: Doc, skip_lemma: bool = False):
        if skip_lemma:
            result = first_doc.similarity(second_doc)
        else:
            second_lemma = second_doc[0].lemma_ if second_doc and second_doc.text.count(' ') == 0 else ''
            first_lemma = first_doc[0].lemma_ if first_doc and first_doc.text.count(' ') == 0 else ''
            result = max(
                first_doc.similarity(second_doc),
                self(first_lemma).similarity(self(second_lemma)) if first_lemma and second_lemma else -1
            )

        if first_doc.text and second_doc.text and not result:
            return partial_ratio(first_doc.text, second_doc.text) / 100

        if result <= 1:
            return result

        if first_doc.vector_norm == 0 or second_doc.vector_norm == 0:
            return -1.0

        return (first_doc.vector @ second_doc.vector) / (first_doc.vector_norm * second_doc.vector_norm)
