import pytest

from bank.formatting import format_inr


@pytest.mark.parametrize('amount, expected', [
    (0, '₹0.00'),
    (5, '₹5.00'),
    (99.5, '₹99.50'),
    (999, '₹999.00'),
    (1000, '₹1,000.00'),
    (12345, '₹12,345.00'),
    (100000, '₹1,00,000.00'),       # 1 lakh
    (1234567.89, '₹12,34,567.89'),   # 12 lakh 34 thousand 567
    (10000000, '₹1,00,00,000.00'),   # 1 crore
    (-500, '-₹500.00'),
    (-100000, '-₹1,00,000.00'),
])
def test_format_inr(amount, expected):
    assert format_inr(amount) == expected


def test_format_inr_rounding_carries_into_rupee_digit():
    assert format_inr(10.999) == '₹11.00'  # 99.9 paise rounds up to 100, which must carry into the rupees
