from datetime import date
from decimal import Decimal

# Historical PPF interest rates data.
# This data can be used by a seeder script to populate the
# `historical_interest_rates` table.
HISTORICAL_PPF_RATES = [
    {
        "start_date": date(1968, 4, 1),
        "end_date": date(1970, 3, 31),
        "rate": Decimal("4.8"),
    },
    {
        "start_date": date(1970, 4, 1),
        "end_date": date(1973, 3, 31),
        "rate": Decimal("5.0"),
    },
    {
        "start_date": date(1973, 4, 1),
        "end_date": date(1974, 3, 31),
        "rate": Decimal("5.3"),
    },
    {
        "start_date": date(1974, 4, 1),
        "end_date": date(1974, 7, 31),
        "rate": Decimal("5.8"),
    },
    {
        "start_date": date(1974, 8, 1),
        "end_date": date(1975, 3, 31),
        "rate": Decimal("7.0"),
    },
    {
        "start_date": date(1975, 4, 1),
        "end_date": date(1977, 3, 31),
        "rate": Decimal("7.0"),
    },
    {
        "start_date": date(1977, 4, 1),
        "end_date": date(1980, 3, 31),
        "rate": Decimal("7.5"),
    },
    {
        "start_date": date(1980, 4, 1),
        "end_date": date(1981, 3, 31),
        "rate": Decimal("8.0"),
    },
    {
        "start_date": date(1981, 4, 1),
        "end_date": date(1983, 3, 31),
        "rate": Decimal("8.5"),
    },
    {
        "start_date": date(1983, 4, 1),
        "end_date": date(1984, 3, 31),
        "rate": Decimal("9.0"),
    },
    {
        "start_date": date(1984, 4, 1),
        "end_date": date(1985, 3, 31),
        "rate": Decimal("9.5"),
    },
    {
        "start_date": date(1985, 4, 1),
        "end_date": date(1986, 3, 31),
        "rate": Decimal("10.0"),
    },
    {
        "start_date": date(1986, 4, 1),
        "end_date": date(1999, 3, 31),
        "rate": Decimal("12.0"),
    },
    {
        "start_date": date(1999, 4, 1),
        "end_date": date(2000, 1, 14),
        "rate": Decimal("12.0"),
    },
    {
        "start_date": date(2000, 1, 15),
        "end_date": date(2001, 2, 28),
        "rate": Decimal("11.0"),
    },
    {
        "start_date": date(2001, 3, 1),
        "end_date": date(2002, 2, 28),
        "rate": Decimal("9.5"),
    },
    {
        "start_date": date(2002, 3, 1),
        "end_date": date(2003, 2, 28),
        "rate": Decimal("9.0"),
    },
    {
        "start_date": date(2003, 3, 1),
        "end_date": date(2011, 11, 30),
        "rate": Decimal("8.0"),
    },
    {
        "start_date": date(2011, 12, 1),
        "end_date": date(2012, 3, 31),
        "rate": Decimal("8.6"),
    },
    {
        "start_date": date(2012, 4, 1),
        "end_date": date(2013, 3, 31),
        "rate": Decimal("8.8"),
    },
    {
        "start_date": date(2013, 4, 1),
        "end_date": date(2016, 3, 31),
        "rate": Decimal("8.7"),
    },
    {
        "start_date": date(2016, 4, 1),
        "end_date": date(2016, 9, 30),
        "rate": Decimal("8.1"),
    },
    {
        "start_date": date(2016, 10, 1),
        "end_date": date(2017, 3, 31),
        "rate": Decimal("8.0"),
    },
    {
        "start_date": date(2017, 4, 1),
        "end_date": date(2017, 6, 30),
        "rate": Decimal("7.9"),
    },
    {
        "start_date": date(2017, 7, 1),
        "end_date": date(2017, 12, 31),
        "rate": Decimal("7.8"),
    },
    {
        "start_date": date(2018, 1, 1),
        "end_date": date(2018, 9, 30),
        "rate": Decimal("7.6"),
    },
    {
        "start_date": date(2018, 10, 1),
        "end_date": date(2019, 6, 30),
        "rate": Decimal("8.0"),
    },
    {
        "start_date": date(2019, 7, 1),
        "end_date": date(2020, 3, 31),
        "rate": Decimal("7.9"),
    },
    {
        "start_date": date(2020, 4, 1),
        "end_date": date(2025, 12, 31),
        "rate": Decimal("7.1"),
    },
]
