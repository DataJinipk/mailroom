from datetime import date, timedelta


def first_monday_of_next_month(run_date: date) -> date:
    """Return the first Monday of the month following run_date."""
    if run_date.month == 12:
        first_of_next = date(run_date.year + 1, 1, 1)
    else:
        first_of_next = date(run_date.year, run_date.month + 1, 1)
    days_until_monday = (0 - first_of_next.weekday()) % 7
    return first_of_next + timedelta(days=days_until_monday)
