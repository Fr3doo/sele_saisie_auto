from sele_saisie_auto.exceptions import DriverError, InvalidConfigError


def test_custom_exceptions_str():
    assert str(DriverError("fail")) == "fail"
    assert str(InvalidConfigError("bad")) == "bad"
