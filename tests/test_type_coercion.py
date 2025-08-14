from ui.pages.tasks import as_int, as_str, as_optional_str


def test_as_str():
    assert as_str("hi") == "hi"
    assert as_str(123) == "123"
    assert as_str(None) == ""


def test_as_optional_str():
    assert as_optional_str("hi") == "hi"
    assert as_optional_str(123) == "123"
    assert as_optional_str("") is None
    assert as_optional_str(None) is None


def test_as_int():
    assert as_int(5) == 5
    assert as_int("7") == 7
    assert as_int("bad", default=1) == 1
    assert as_int(None, default=2) == 2
