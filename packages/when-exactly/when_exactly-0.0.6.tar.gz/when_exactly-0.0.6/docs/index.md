# When-Exactly

An expressive and intuitive library for working with dates.

## Rationale

Why are rogrammers are restricted to working with _date-time_
and _date_ objects while needing to work with dates?

People tend to think and communicate about time in terms of
_years_, _months_, _weeks_, _days_, _hours_, _minutes_, etc.

When-Exactly is a library that aims to bring these types into the hands of developers,
so they can write more expressive code when working with dates.

## Overview

```python
>>> import when_exactly as we

>>> year = we.Year(2025) # the year 2025
>>> year
Year(2025)

>>> month = year.month(1) # month 1 (January) of the year
>>> month
Month(2025, 1)

>>> day = we.Day(2025, 12, 25) # December 25, 2025
>>> day
Day(2025, 12, 25)

>>> day.month # the month that the day is a part of
Month(2025, 12)

>>> day.week # the week that the day is a part of
Week(2025, 52)

```
