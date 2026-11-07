import pytest

from app.modules.readings.domain.exceptions import InvalidQuestion
from app.modules.readings.domain.question_policy import clean_question


def test_trims_and_collapses_whitespace():
    assert clean_question("  Tình   yêu\n\nthế nào?  ", 300) == "Tình yêu thế nào?"


@pytest.mark.parametrize("text", ["", "   ", "\n\t "])
def test_rejects_blank(text):
    with pytest.raises(InvalidQuestion):
        clean_question(text, 300)


def test_length_limit_is_inclusive():
    assert len(clean_question("a" * 300, 300)) == 300
    with pytest.raises(InvalidQuestion):
        clean_question("a" * 301, 300)
