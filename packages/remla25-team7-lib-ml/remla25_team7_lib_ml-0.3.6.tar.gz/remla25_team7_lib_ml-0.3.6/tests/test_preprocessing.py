import pytest
from lib_ml.preprocessing import clean_review, tokenize_review

def test_clean_review_strips_punctuation():
    assert clean_review("Hello, WORLD!!!") == "hello world"

def test_tokenize_keeps_not_and_stems():
    toks = tokenize_review("This is not good.")
    assert "not" in toks
    assert any(tok.startswith("good") for tok in toks)
