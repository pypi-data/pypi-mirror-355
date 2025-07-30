import pytest


@pytest.mark.parametrize(
    ("x", "expected"),
    [
        (2, 4),
        (3, 9),
        (4, 16),
        (5, 25),
    ],
)
def test_square(x: int, expected: int) -> None:
    from vdag import square
    assert square(x) == expected
