import pytest
import saltext.mqtt_return.returners.mqtt_return_mod as mqtt_return_returner


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"this_does_not_exist.please_replace_it": lambda: True},
    }
    return {
        mqtt_return_returner: module_globals,
    }


def test_replace_this_this_with_something_meaningful():
    assert "this_does_not_exist.please_replace_it" in mqtt_return_returner.__salt__
    assert mqtt_return_returner.__salt__["this_does_not_exist.please_replace_it"]() is True
