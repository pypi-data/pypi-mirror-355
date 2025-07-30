from gensim.models.fasttext import FastText
from numpy import average
from gensim.test.utils import datapath
from FinAnalytics.E.BankStatement.load_extractor import Pipeline
from FinAnalytics.E.BankStatement.extract_pdf import diff_check
from pathlib import Path
from tempfile import mkstemp
from spacy import load
from os import close
from typing import Optional
from loguru import logger
from FinAnalytics.types_used import what_we_need, map_needs, model_name


def is_wise_score(score: float):
    return score > .6


class VerifyModel:
    def __init__(self):
        self.pipeline = Pipeline()
        self.known_conversions = {}
        self.sim_tests = (
            ('cheque', "cheque number"),
            ('cheque no.', 'cheque number'),
            ('cheque no', 'cheque number'),
            ('txn date', 'transaction time'),
            ('date', 'transaction time'),
            ('value date', 'timestamp'),
            ('txn time', 'transaction time'),
            ('time', 'transaction time'),
            ('desc', 'description'),
            ('notes', 'message'),
            ('txn', 'transaction'),
            ('debited', 'debit'),
            ('deposit', 'credit'),
            ('credited', 'credit'),
            ('withdraw', 'debit'),
            ('withdrawal', 'debit'),
            ('particulars', 'description'),
            ('account balance', 'balance'),
            ('bank balance', 'balance'),
            ('balance', 'balance'),  # just for the same word test
        )

    def converted(self, word):
        self.known_conversions[word] = self.known_conversions.get(word, self.pipeline(word, force_convert=True))
        return self.known_conversions[word]

    def sim_test(self, word_1: str, word_2: str, log: bool = False):
        result = self.pipeline.sim_check(self.converted(word_1), self.converted(word_2))
        if not is_wise_score(result) and log:
            logger.error(f"❌ sim_test_result: {word_1} vs {word_2}: {round(result * 100, 2)}%")
        return result

    def diff_tests(self, word_1, sim_to, *compared_to):
        main_score = self.sim_test(word_1, sim_to)
        result = True
        r_score = -1
        r_index = -1
        scores = []

        for right_index, right_ in enumerate(compared_to):
            r_score = self.sim_test(word_1, right_, False)
            scores.append(r_score)
            result = not diff_check(main_score, r_score, sim_to, right_, word_1)
            r_index = right_index
            if not result:
                break

        if not result:
            logger.error(
                f"❌ diff_test_result: {word_1} vs {sim_to}: {round(main_score * 100, 2)}% "
                f"with {round(r_score * 100, 2)}% from {compared_to[r_index]}"
            )
        return result

    def test(self):
        sim_test_results = [self.sim_test(*_, log=True) for _ in self.sim_tests]

        # right side where we compare are the words where we have it "what_we_know"
        diff_test_cases = (
            [test[0], test[1], *(_ for _ in what_we_need if map_needs[_] != map_needs[test[1]])]
            for test in self.sim_tests if test[1] in map_needs
        )
        diff_test_results = [self.diff_tests(*_) for _ in diff_test_cases]

        avg_score = average(sim_test_results)
        min_score = min(sim_test_results)

        if not is_wise_score(min_score):
            logger.warning(
                "❌ Low Accuracy found: {}%, Average Result from results: {}",
                round(float(min_score) * 100, 2), round(float(avg_score) * 100, 2)
            )
            for i, value in enumerate(self.sim_tests):
                if is_wise_score(sim_test_results[i]):
                    logger.info(f"{value[0]} with {value[1]}: {round(float(sim_test_results[i]) * 100, 2)}%")
        else:
            logger.info("✅ Good Accuracy based on few tests: {}%", round(float(avg_score) * 100, 2))

        failed = diff_test_results.count(False)
        if failed >= 1:
            logger.warning("❌ DIFF. Test Results: Failed Count: {}", failed)
            for i, test in enumerate(diff_test_cases):
                if diff_test_results[i]:
                    logger.info(f"✅ {test}")
        else:
            logger.info("✅ DIFF. Test Results: Passed Count: {}", len(diff_test_results) - failed)


def load_custom_vectors(nlp, vec_path):
    count = 0
    with open(vec_path, "r", encoding="utf8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            word = parts[0]
            vector = [float(v) for v in parts[1:]]
            nlp.vocab.set_vector(word, vector)
            count += 1
    logger.info(f"✅ Loaded {count} vectors into spaCy.")


def train_model(save_in: Optional[Path | str] = None):
    corpus_file = datapath(str(Path(__file__).parent / "train_data.cor"))
    model = FastText(min_count=2, vector_size=300, window=10)
    model.build_vocab(corpus_file=corpus_file)

    # training it thrice to get better vectors
    model.train(
        corpus_file=corpus_file, epochs=model.epochs * 20,
        total_examples=model.corpus_count, total_words=model.corpus_total_words,
    )

    fd, path = mkstemp(prefix="bank-statement-vectors-")

    try:
        model.wv.save_word2vec_format(path, binary=False)
        pipeline = load("en_core_web_md")
        load_custom_vectors(pipeline, path)
        pipeline.to_disk((Path(save_in) if save_in else Path.cwd()) / model_name)

        VerifyModel().test()
    except Exception as error:
        raise error
    finally:
        close(fd)


if __name__ == "__main__":
    train_model()
