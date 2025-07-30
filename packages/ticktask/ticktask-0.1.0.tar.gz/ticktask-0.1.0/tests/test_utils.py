import typing

import pytest
import time
import datetime
from src.ticktask import deserialize_callable, serialize_callable


def mock_callable(arg1: int, arg2: int):
    return arg1 + arg2


class MockClass:
    def mock_callable(self, arg1: int, arg2: int):
        return arg1 + arg2


def test_serialize_callable():
    test_callable = mock_callable
    test_module = "test_utils"
    test_qualname = "mock_callable"
    serialized_dict = serialize_callable(test_callable)
    assert serialized_dict['module'] == test_module
    assert serialized_dict['qualname'] == test_qualname


def test_deserialize_callable():
    test_module = "test_utils"
    test_qualname = "mock_callable"
    serialized_dict = {
        'module': test_module,
        'qualname': test_qualname,
    }
    restored_callable = deserialize_callable(serialized_dict)
    assert restored_callable(1, 1) == 2


def test_serialize_callable_class():
    test_callable = MockClass.mock_callable
    test_module = "test_utils"
    test_qualname = "MockClass.mock_callable"
    test_instance_required = True
    serialized_dict = serialize_callable(test_callable)
    assert serialized_dict['module'] == test_module
    assert serialized_dict['qualname'] == test_qualname
    assert serialized_dict['instance_required'] == test_instance_required


def test_deserialize_callable_class():
    test_module = "test_utils"
    test_qualname = "MockClass.mock_callable"
    test_instance_required = True
    serialized_dict = {
        'module': test_module,
        'qualname': test_qualname,
        'instance_required': test_instance_required,
    }
    restored_callable = deserialize_callable(serialized_dict)
    assert restored_callable(1, 1) == 2


if __name__ == "__main__":
    pytest.main()