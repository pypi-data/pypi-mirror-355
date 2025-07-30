import pytz

from datetime import datetime, date, time, timedelta
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse


class ChronoUtils:

    @staticmethod
    def str_to_datetime(dt_str, fmt="%Y-%m-%d %H:%M:%S", tz=None):
        """Convert string to datetime (with optional timezone)."""
        dt = parse(str(dt_str))
        if tz:
            dt = timezone.localtime(dt, pytz.timezone(tz))
        return dt

    @staticmethod
    def datetime_to_str(dt, fmt="%Y-%m-%d %H:%M:%S"):
        """Convert datetime to string."""
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt)
        return dt.strftime(fmt)

    @staticmethod
    def datetime_to_str_tz(dt, fmt="%Y-%m-%d %H:%M:%S", tz="UTC"):
        """Convert datetime to string with timezone."""
        return timezone.localtime(dt, pytz.timezone(tz)).strftime(fmt)

    @staticmethod
    def date_to_datetime(d, tz=None):
        """Convert date to datetime at midnight."""
        dt = datetime.combine(d, time.min)
        if tz:
            return timezone.make_aware(dt, tz)
        return dt

    @staticmethod
    def datetime_to_date(dt):
        """Convert datetime to date."""
        return dt.date()

    @staticmethod
    def to_utc(dt):
        """Convert datetime to UTC."""
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt)
        return timezone.localtime(dt, timezone.utc)

    @staticmethod
    def from_utc(dt, tz):
        """Convert datetime from UTC to given timezone."""
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.utc)
        return timezone.localtime(dt, tz)

    @staticmethod
    def timestamp_to_datetime(ts, tz=None):
        """Convert timestamp to datetime."""
        dt = datetime.fromtimestamp(ts)
        if tz:
            dt = timezone.make_aware(dt, tz)
        return dt

    @staticmethod
    def datetime_to_timestamp(dt):
        """Convert datetime to timestamp."""
        if timezone.is_aware(dt):
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.timestamp()

    @staticmethod
    def parse_iso(dt_str, tz=None):
        """Parse ISO-format string to datetime."""
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None and tz:
            dt = timezone.make_aware(dt, tz)
        return dt

    @staticmethod
    def to_iso(dt):
        """Convert datetime to ISO string."""
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt)
        return dt.isoformat()

    @staticmethod
    def get_day_bounds(d, tz=None):
        """Get start and end of the day for a date."""
        if isinstance(d, datetime):
            d = d.date()
        start = datetime.combine(d, time.min)
        end = datetime.combine(d, time.max)
        if tz:
            start = timezone.make_aware(start, tz)
            end = timezone.make_aware(end, tz)
        return start, end

    @staticmethod
    def get_week_bounds(d, tz=None, start_of_week=0):
        """
        Get week boundaries (start/end).
        start_of_week: 0 - Monday, 6 - Sunday
        """
        if isinstance(d, datetime):
            d = d.date()
        start = d - timedelta(days=(d.weekday() - start_of_week) % 7)
        end = start + timedelta(days=6)
        return (
            ChronoUtils.get_day_bounds(start, tz)[0],
            ChronoUtils.get_day_bounds(end, tz)[1],
        )

    @staticmethod
    def add_weeks(dt, weeks):
        """Add N weeks."""
        return dt + timedelta(weeks=weeks)

    @staticmethod
    def sub_weeks(dt, weeks):
        """Subtract N weeks."""
        return dt - timedelta(weeks=weeks)

    @staticmethod
    def add_months(dt, months):
        """Add N months."""
        return dt + relativedelta(months=months, day=0)

    @staticmethod
    def sub_months(dt, months):
        """Subtract N months."""
        return dt - relativedelta(months=months, day=0)

    @staticmethod
    def add_years(dt, years):
        """Add N years."""
        return dt + relativedelta(years=years, months=0)

    @staticmethod
    def sub_years(dt, years):
        """Subtract N years."""
        return dt - relativedelta(years=years, months=0)

    @staticmethod
    def diff_in_weeks(dt1, dt2):
        """Absolute difference in weeks (integer, no remainder)."""
        return abs((dt1 - dt2).days) // 7

    @staticmethod
    def diff_in_months(dt1, dt2):
        """Absolute difference in months."""
        rd = relativedelta(dt1, dt2)
        return abs(rd.years * 12 + rd.months)

    @staticmethod
    def diff_in_years(dt1, dt2):
        """Absolute difference in years."""
        rd = relativedelta(dt1, dt2)
        return abs(rd.years)

    @staticmethod
    def diff_in_days(dt1, dt2):
        """
        Absolute difference in days between two dates/datetimes.
        Returns an integer (abs).
        """
        if isinstance(dt1, datetime):
            dt1 = dt1.date()
        if isinstance(dt2, datetime):
            dt2 = dt2.date()
        return abs((dt1 - dt2).days)
