def format_inr(amount: float) -> str:
    """Format a dollar-style float as Indian Rupees with Indian digit
    grouping (lakh/crore: last 3 digits, then groups of 2), e.g.
    1234567.89 -> '₹12,34,567.89', 100000 -> '₹1,00,000.00'."""
    negative = amount < 0
    amount = abs(amount)
    rupees = int(amount)
    paise = round((amount - rupees) * 100)
    if paise == 100:  # rounding carried over, e.g. 99.999
        rupees += 1
        paise = 0

    digits = str(rupees)
    if len(digits) > 3:
        last3, rest = digits[-3:], digits[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        grouped = ','.join(groups) + ',' + last3
    else:
        grouped = digits

    formatted = f'₹{grouped}.{paise:02d}'
    return f'-{formatted}' if negative else formatted
