import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any


# 1. Basic test
@pytest.mark.smoke
def test_addition():
    """
    This test is used to test the addition of two numbers.
    """
    assert 1 + 1 == 2

# 2. Failing test
@pytest.mark.smoke
def test_fail_case():
    """
    This test is used to test the failure of a test case.
    """
    assert "abc".upper() == "ABC"

# 3. Parametrized test
@pytest.mark.smoke
@pytest.mark.parametrize("a,b,result", [
    (2, 3, 5),
    (10, 5, 15),
    (1, 1, 2)
])
def test_add(a, b, result):
    """
    This test is used to test the addition of two numbers.
    """
    assert a + b == result

# 4. Test for exception
@pytest.mark.smoke
def test_zero_division():
    """
    This test is used to test the division of two numbers.
    """
    with pytest.raises(ZeroDivisionError):
        _ = 1 / 0

# 5. Test with fixture
@pytest.fixture
def sample_list():
    return [1, 2, 3]

@pytest.mark.smoke
def test_list_append(sample_list):
    """
    This test is used to test the appending of a number to a list.
    """
    sample_list.append(4)
    assert sample_list == [1, 2, 3, 4, 5]

# 6. Skip test
@pytest.mark.smoke
@pytest.mark.skip(reason="Skipping this test for demo")
def test_skip_example():
    """
    This test is used to test the skipping of a test case.
    """
    assert False

# 7. Expected failure
@pytest.mark.smoke
@pytest.mark.xfail(reason="Known bug, will fix later")
@pytest.mark.skip(reason="Skipping this test for demo")
def test_known_bug():
    """
    This test is used to test the known bug of a test case.
    """
    assert 2 * 2 == 5

# 8. Custom marker (e.g., smoke)
@pytest.mark.smoke
def test_login_smoke():
    """
    This test is used to test the login of a user.
    """
    assert "user" in "user123"

# 9. Test string methods
@pytest.mark.smoke
def test_string_methods():
    """
    This test is used to test the string methods.
    """
    assert "hello world".title() == "Hello World"

# 10. Test dict behavior
@pytest.mark.smoke
def test_dict_merge():
    """
    This test is used to test the merging of two dictionaries.
    """
    d1 = {"a": 1}
    d2 = {"b": 2}
    d1.update(d2)
    assert d1 == {"a": 1, "b": 2}

@pytest.mark.smoke
def test_new_test():
    """
    This test is used to test the new test case.
    """
    assert 1 + 1 == 20

@pytest.mark.smoke
def test_new_test2():
    """
    This test is used to test the new test case.
    """
    assert 1 + 1 == 3

@pytest.mark.smoke
def test_new_test3():
    """
    This test is used to test the new test case.
    """
    assert 1 + 1 == 3

@pytest.mark.smoke
def test_new_test4():
    """
    This test is used to test the new test case.
    """
    assert 1 + 1 == 3

@pytest.mark.smoke
def test_new_test5():
    assert 1 + 1 == 3


class TestStringOperations:
    """Test suite for string manipulation operations."""
    
    @pytest.mark.smoke
    def test_string_concatenation(self):
        """Test basic string concatenation functionality."""
        str1 = "Hello"
        str2 = "World"
        assert str1 + " " + str2 == "Hello World"
    
    @pytest.mark.smoke
    def test_string_formatting(self):
        """Test different string formatting methods."""
        name = "Alice"
        age = 30
        assert f"{name} is {age} years old" == "Alice is 30 years old"
        assert "{} is {} years old".format(name, age) == "Alice is 30 years old"
    
    @pytest.mark.smoke
    @pytest.mark.parametrize("input_str,expected", [
        ("hello", "HELLO"),
        ("WORLD", "WORLD"),
        ("", ""),
        ("123", "123")
    ])
    def test_string_case_conversion(self, input_str: str, expected: str):
        """Test string case conversion methods with various inputs."""
        assert input_str.upper() == expected

class TestListOperations:
    """Test suite for list manipulation operations."""
    
    @pytest.fixture
    def sample_list(self) -> List[int]:
        """Fixture providing a sample list for testing."""
        return [1, 2, 3, 4, 5]
    
    @pytest.mark.smoke
    def test_list_slicing(self, sample_list: List[int]):
        """Test list slicing operations."""
        assert sample_list[1:3] == [2, 3]
        assert sample_list[::-1] == [5, 4, 3, 2, 1]
    
    @pytest.mark.smoke
    def test_list_comprehension(self):
        """Test list comprehension functionality."""
        numbers = [1, 2, 3, 4, 5]
        squares = [n**2 for n in numbers]
        assert squares == [1, 4, 9, 16, 25]
    
    @pytest.mark.smoke
    @pytest.mark.parametrize("input_list,expected", [
        ([1, 2, 3], 6),
        ([], 0),
        ([5], 5),
        ([-1, -2, -3], -6)
    ])
    def test_list_sum(self, input_list: List[int], expected: int):
        """Test list sum operation with various inputs."""
        assert sum(input_list) == expected


class TestDictionaryOperations:
    """Test suite for dictionary operations."""
    
    @pytest.fixture
    def sample_dict(self) -> Dict[str, Any]:
        """Fixture providing a sample dictionary for testing."""
        return {"a": 1, "b": 2, "c": 3}
    
    @pytest.mark.smoke
    def test_dict_get(self, sample_dict: Dict[str, Any]):
        """Test dictionary get method with default values."""
        assert sample_dict.get("a") == 1
        assert sample_dict.get("d", 0) == 0
    
    @pytest.mark.smoke
    def test_dict_comprehension(self):
        """Test dictionary comprehension functionality."""
        numbers = [1, 2, 3, 4, 5]
        square_dict = {n: n**2 for n in numbers}
        assert square_dict == {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}
    
    @pytest.mark.smoke
    @pytest.mark.parametrize("dict1,dict2,expected", [
        ({"a": 1}, {"b": 2}, {"a": 1, "b": 2}),
        ({}, {"a": 1}, {"a": 1}),
        ({"a": 1}, {}, {"a": 1}),
        ({"a": 1}, {"a": 2}, {"a": 2})
    ])
    def test_dict_update(self, dict1: Dict[str, Any], dict2: Dict[str, Any], expected: Dict[str, Any]):
        """Test dictionary update operation with various inputs."""
        dict1.update(dict2)
        assert dict1 == expected

class TestErrorHandling:
    """Test suite for error handling scenarios."""
    
    @pytest.mark.smoke
    def test_custom_exception(self):
        """Test custom exception handling."""
        class CustomError(Exception):
            pass
        
        with pytest.raises(CustomError):
            raise CustomError("Custom error message")
    
    @pytest.mark.smoke
    @pytest.mark.parametrize("input_value,expected_exception", [
        ("abc", ValueError),
        ("", ValueError),
        ("123", ValueError)
    ])
    def test_value_error(self, input_value: str, expected_exception: Exception):
        """Test value error handling with various inputs."""
        with pytest.raises(expected_exception):
            int(input_value)
    
    @pytest.mark.smoke
    def test_multiple_exceptions(self):
        """Test handling of multiple exception types."""
        with pytest.raises((ValueError, TypeError)):
            int("abc")
