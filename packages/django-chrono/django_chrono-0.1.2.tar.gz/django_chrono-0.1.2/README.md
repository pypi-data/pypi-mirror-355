# django-chrono

django-chrono is a helper class for date and time operations in Django projects.

### Usage Examples


#### 1. String ↔ Datetime

```python
from django_chrono import ChronoUtils

dt = ChronoUtils.str_to_datetime("2025-06-07 16:30:00")
dt_str = ChronoUtils.datetime_to_str(dt, fmt="%d.%m.%Y %H:%M")
# Result: '07.06.2025 16:30'
```

#### 2. Date ↔ Datetime

```python
import datetime
from django_chrono import ChronoUtils

d = datetime.date(2025, 6, 7)
dt = ChronoUtils.date_to_datetime(d)  # 2025-06-07 00:00:00
d2 = ChronoUtils.datetime_to_date(dt) # 2025-06-07
```

#### 3. Timestamps

```python
dt = ChronoUtils.timestamp_to_datetime(1759991100)
ts = ChronoUtils.datetime_to_timestamp(dt)
```

#### 4. Time Zone Conversion

```python
import pytz
from django.utils import timezone

dt = ChronoUtils.str_to_datetime("2025-06-07 12:00:00", tz=pytz.timezone('Europe/Sofia'))
dt_utc = ChronoUtils.to_utc(dt)            # Convert to UTC
dt_local = ChronoUtils.from_utc(dt_utc, pytz.timezone('Europe/Sofia'))  # Convert back
```

#### 5. ISO Format

```python
dt = ChronoUtils.parse_iso("2025-06-07T14:15:00")
iso_str = ChronoUtils.to_iso(dt)
```

#### 6. Day/Week Boundaries

```python
today = datetime.date.today()
start_day, end_day = ChronoUtils.get_day_bounds(today)
start_week, end_week = ChronoUtils.get_week_bounds(today, start_of_week=0)  # Monday
```

#### 7. Add/Subtract Weeks, Months, Years

```python
from django_chrono import ChronoUtils

dt = datetime.date(2025, 6, 7)
dt_plus_2w = ChronoUtils.add_weeks(dt, 2)   # +2 weeks
dt_minus_1m = ChronoUtils.sub_months(dt, 1) # -1 month
dt_plus_3y = ChronoUtils.add_years(dt, 3)   # +3 years
```

#### 8. Calculate Difference

```python
d1 = datetime.date(2024, 6, 7)
d2 = datetime.date(2025, 6, 7)
w_diff = ChronoUtils.diff_in_weeks(d2, d1)    # 52
m_diff = ChronoUtils.diff_in_months(d2, d1)   # 12
y_diff = ChronoUtils.diff_in_years(d2, d1)    # 1
```