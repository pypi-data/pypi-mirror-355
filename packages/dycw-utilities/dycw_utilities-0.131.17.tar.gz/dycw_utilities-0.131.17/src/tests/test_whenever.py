from __future__ import annotations

import datetime as dt
from datetime import timezone
from re import escape
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

from hypothesis import assume, example, given
from hypothesis.strategies import (
    dates,
    datetimes,
    integers,
    just,
    sampled_from,
    timedeltas,
    times,
    timezones,
)
from pytest import raises
from whenever import DateTimeDelta

from tests.conftest import SKIPIF_CI_AND_WINDOWS
from utilities.datetime import (
    _MICROSECONDS_PER_DAY,
    _MICROSECONDS_PER_SECOND,
    DAY,
    MICROSECOND,
    SECOND,
    maybe_sub_pct_y,
    parse_two_digit_year,
    serialize_compact,
)
from utilities.hypothesis import (
    assume_does_not_raise,
    datetime_durations,
    plain_datetimes,
    zoned_datetimes,
)
from utilities.tzdata import HongKong
from utilities.whenever import (
    MAX_SERIALIZABLE_TIMEDELTA,
    MIN_SERIALIZABLE_TIMEDELTA,
    ParseDateError,
    ParseDateTimeError,
    ParseDurationError,
    ParsePlainDateTimeError,
    ParseTimeError,
    ParseZonedDateTimeError,
    SerializeDurationError,
    SerializePlainDateTimeError,
    SerializeTimeDeltaError,
    SerializeZonedDateTimeError,
    _CheckValidZonedDateTimeUnequalError,
    _ParseTimedeltaNanosecondError,
    _ParseTimedeltaParseError,
    _to_datetime_delta,
    _ToDateTimeDeltaError,
    check_valid_zoned_datetime,
    parse_date,
    parse_datetime,
    parse_duration,
    parse_plain_datetime,
    parse_time,
    parse_timedelta,
    parse_zoned_datetime,
    serialize_date,
    serialize_datetime,
    serialize_duration,
    serialize_plain_datetime,
    serialize_time,
    serialize_timedelta,
    serialize_zoned_datetime,
)
from utilities.zoneinfo import UTC, get_time_zone_name

if TYPE_CHECKING:
    from utilities.types import Duration


_TIMEDELTA_MICROSECONDS = int(1e18) * MICROSECOND
_TIMEDELTA_OVERFLOW = dt.timedelta(days=106751991, seconds=14454, microseconds=775808)


@SKIPIF_CI_AND_WINDOWS
class TestCheckValidZonedDateTime:
    @given(
        datetime=sampled_from([
            dt.datetime(1951, 4, 1, 3, tzinfo=HongKong),
            dt.datetime(1951, 4, 1, 5, tzinfo=HongKong),
        ])
    )
    def test_main(self, *, datetime: dt.datetime) -> None:
        check_valid_zoned_datetime(datetime)

    def test_error(self) -> None:
        datetime = dt.datetime(1951, 4, 1, 4, tzinfo=HongKong)
        with raises(
            _CheckValidZonedDateTimeUnequalError,
            match=escape(
                "Zoned datetime must be valid; got 1951-04-01 04:00:00+08:00 != 1951-04-01 05:00:00+09:00"
            ),
        ):
            check_valid_zoned_datetime(datetime)


class TestSerializeAndParseDate:
    @given(date=dates())
    def test_main(self, *, date: dt.date) -> None:
        serialized = serialize_date(date)
        result = parse_date(serialized)
        assert result == date

    @given(year=integers(0, 99), date=dates())
    def test_yymmdd(self, *, year: int, date: dt.date) -> None:
        with assume_does_not_raise(ValueError):
            date_use = date.replace(parse_two_digit_year(year))
        serialized = date_use.strftime("%y%m%d")
        result = parse_date(serialized)
        assert result == date_use

    @given(date=dates())
    def test_yyyymmdd(self, *, date: dt.date) -> None:
        serialized = serialize_compact(date)
        result = parse_date(serialized)
        assert result == date

    def test_error_parse(self) -> None:
        with raises(ParseDateError, match="Unable to parse date; got 'invalid'"):
            _ = parse_date("invalid")


class TestSerializeAndParseDateTime:
    @given(
        datetime=plain_datetimes()
        | zoned_datetimes(time_zone=timezones() | just(dt.UTC), valid=True)
    )
    @SKIPIF_CI_AND_WINDOWS
    def test_main(self, *, datetime: dt.datetime) -> None:
        serialized = serialize_datetime(datetime)
        result = parse_datetime(serialized)
        assert result == datetime

    def test_error_parse(self) -> None:
        with raises(
            ParseDateTimeError, match="Unable to parse datetime; got 'invalid'"
        ):
            _ = parse_datetime("invalid")


class TestSerializeAndParseDuration:
    @given(duration=datetime_durations())
    def test_main(self, *, duration: Duration) -> None:
        with assume_does_not_raise(SerializeDurationError):
            serialized = serialize_duration(duration)
        with assume_does_not_raise(ParseDurationError):
            result = parse_duration(serialized)
        assert result == duration

    def test_error_parse(self) -> None:
        with raises(
            ParseDurationError, match="Unable to parse duration; got 'invalid'"
        ):
            _ = parse_duration("invalid")

    @given(duration=sampled_from([_TIMEDELTA_MICROSECONDS, _TIMEDELTA_OVERFLOW]))
    def test_error_serialize(self, *, duration: Duration) -> None:
        with raises(
            SerializeDurationError, match="Unable to serialize duration; got .*"
        ):
            _ = serialize_duration(duration)


class TestSerializeAndParsePlainDateTime:
    @given(datetime=datetimes())
    def test_main(self, *, datetime: dt.datetime) -> None:
        serialized = serialize_plain_datetime(datetime)
        result = parse_plain_datetime(serialized)
        assert result == datetime

    @given(datetime=plain_datetimes(round_="standard", timedelta=SECOND))
    def test_compact_no_microseconds(self, *, datetime: dt.datetime) -> None:
        assert datetime.microsecond == 0
        serialized = datetime.strftime(maybe_sub_pct_y("%Y%m%dT%H%M%S"))
        result = parse_plain_datetime(serialized)
        assert result == datetime

    @given(datetime=datetimes())
    def test_compact_with_microseconds(self, *, datetime: dt.datetime) -> None:
        _ = assume(datetime.microsecond != 0)
        serialized = datetime.strftime(maybe_sub_pct_y("%Y%m%dT%H%M%S.%f"))
        result = parse_plain_datetime(serialized)
        assert result == datetime

    def test_error_parse(self) -> None:
        with raises(
            ParsePlainDateTimeError,
            match="Unable to parse plain datetime; got 'invalid'",
        ):
            _ = parse_plain_datetime("invalid")

    def test_error_serialize(self) -> None:
        datetime = dt.datetime(2000, 1, 1, tzinfo=UTC)
        with raises(
            SerializePlainDateTimeError,
            match="Unable to serialize plain datetime; got .*",
        ):
            _ = serialize_plain_datetime(datetime)


class TestSerializeAndParseTime:
    @given(time=times())
    def test_main(self, *, time: dt.time) -> None:
        serialized = serialize_time(time)
        result = parse_time(serialized)
        assert result == time

    def test_error_parse(self) -> None:
        with raises(ParseTimeError, match="Unable to parse time; got 'invalid'"):
            _ = parse_time("invalid")


class TestSerializeAndParseTimedelta:
    @given(
        timedelta=timedeltas(
            min_value=MIN_SERIALIZABLE_TIMEDELTA, max_value=MAX_SERIALIZABLE_TIMEDELTA
        )
    )
    @example(timedelta=int(1e6) * DAY)
    @example(timedelta=MICROSECOND)
    @example(timedelta=-DAY)
    @example(timedelta=-DAY + MICROSECOND)
    def test_main(self, *, timedelta: dt.timedelta) -> None:
        serialized = serialize_timedelta(timedelta)
        result = parse_timedelta(serialized)
        assert result == timedelta

    @given(timedelta=timedeltas(min_value=MICROSECOND))
    def test_min_serializable(self, *, timedelta: dt.timedelta) -> None:
        _ = serialize_timedelta(MIN_SERIALIZABLE_TIMEDELTA)
        with assume_does_not_raise(OverflowError):
            offset = MIN_SERIALIZABLE_TIMEDELTA - timedelta
        with raises(SerializeTimeDeltaError):
            _ = serialize_timedelta(offset)

    @given(timedelta=timedeltas(min_value=MICROSECOND))
    def test_max_serializable(self, *, timedelta: dt.timedelta) -> None:
        _ = serialize_timedelta(MAX_SERIALIZABLE_TIMEDELTA)
        with assume_does_not_raise(OverflowError):
            offset = MAX_SERIALIZABLE_TIMEDELTA + timedelta
        with raises(SerializeTimeDeltaError):
            _ = serialize_timedelta(offset)

    def test_error_parse(self) -> None:
        with raises(
            _ParseTimedeltaParseError, match="Unable to parse timedelta; got 'invalid'"
        ):
            _ = parse_timedelta("invalid")

    def test_error_parse_nano_seconds(self) -> None:
        with raises(
            _ParseTimedeltaNanosecondError,
            match="Unable to parse timedelta; got 333 nanoseconds",
        ):
            _ = parse_timedelta("PT0.111222333S")

    @given(timedelta=sampled_from([_TIMEDELTA_MICROSECONDS, _TIMEDELTA_OVERFLOW]))
    def test_error_serialize(self, *, timedelta: dt.timedelta) -> None:
        with raises(
            SerializeTimeDeltaError, match="Unable to serialize timedelta; got .*"
        ):
            _ = serialize_timedelta(timedelta)


class TestSerializeAndParseZonedDateTime:
    @given(datetime=zoned_datetimes(valid=True))
    @SKIPIF_CI_AND_WINDOWS
    def test_main(self, *, datetime: dt.datetime) -> None:
        serialized = serialize_zoned_datetime(datetime)
        result = parse_zoned_datetime(serialized)
        assert result == datetime

    @given(
        datetime=zoned_datetimes(
            time_zone=just(dt.UTC), round_="standard", timedelta=SECOND, valid=True
        )
    )
    @SKIPIF_CI_AND_WINDOWS
    def test_compact_no_microseconds(self, *, datetime: dt.datetime) -> None:
        assert datetime.microsecond == 0
        part1 = datetime.strftime(maybe_sub_pct_y("%Y%m%dT%H%M%S"))
        assert isinstance(datetime.tzinfo, ZoneInfo | timezone)
        part2 = get_time_zone_name(datetime.tzinfo)
        serialized = f"{part1}[{part2}]"
        result = parse_zoned_datetime(serialized)
        assert result == datetime

    @given(datetime=zoned_datetimes(time_zone=just(dt.UTC), valid=True))
    @SKIPIF_CI_AND_WINDOWS
    def test_compact_with_microseconds(self, *, datetime: dt.datetime) -> None:
        _ = assume(datetime.microsecond != 0)
        part1 = datetime.strftime(maybe_sub_pct_y("%Y%m%dT%H%M%S.%f"))
        assert isinstance(datetime.tzinfo, ZoneInfo | timezone)
        part2 = get_time_zone_name(datetime.tzinfo)
        serialized = f"{part1}[{part2}]"
        result = parse_zoned_datetime(serialized)
        assert result == datetime

    @given(datetime=plain_datetimes())
    @SKIPIF_CI_AND_WINDOWS
    def test_utc(self, *, datetime: dt.datetime) -> None:
        datetime1, datetime2 = [datetime.astimezone(tz) for tz in [UTC, dt.UTC]]
        serialized1, serialized2 = map(serialize_zoned_datetime, [datetime1, datetime2])
        assert serialized1 == serialized2
        parsed = parse_zoned_datetime(serialized1)
        assert abs(parsed - datetime1) <= SECOND
        assert abs(parsed - datetime2) <= SECOND
        assert parsed.tzinfo is UTC

    def test_error_parse(self) -> None:
        with raises(
            ParseZonedDateTimeError,
            match="Unable to parse zoned datetime; got 'invalid'",
        ):
            _ = parse_zoned_datetime("invalid")

    def test_error_serialize(self) -> None:
        datetime = dt.datetime(2000, 1, 1).astimezone(None)
        with raises(
            SerializeZonedDateTimeError,
            match="Unable to serialize zoned datetime; got 2000-01-01 00:00:00",
        ):
            _ = serialize_zoned_datetime(datetime)


class TestToDateTimeDelta:
    @given(days=integers(), microseconds=integers())
    def test_main(self, *, days: int, microseconds: int) -> None:
        with assume_does_not_raise(OverflowError):
            timedelta = dt.timedelta(days=days, microseconds=microseconds)
        init_total_micro = _MICROSECONDS_PER_DAY * days + microseconds
        with assume_does_not_raise(_ToDateTimeDeltaError):
            result = _to_datetime_delta(timedelta)
        comp_month, comp_day, comp_sec, comp_nano = result.in_months_days_secs_nanos()
        assert comp_month == 0
        comp_micro, remainder = divmod(comp_nano, 1000)
        assert remainder == 0
        result_total_micro = (
            _MICROSECONDS_PER_DAY * comp_day
            + _MICROSECONDS_PER_SECOND * comp_sec
            + comp_micro
        )
        assert init_total_micro == result_total_micro

    def test_mixed_sign(self) -> None:
        timedelta = dt.timedelta(days=-1, seconds=1)
        result = _to_datetime_delta(timedelta)
        expected = DateTimeDelta(seconds=timedelta.total_seconds())
        assert result == expected

    def test_close_to_overflow(self) -> None:
        timedelta = dt.timedelta(days=104250, microseconds=1)
        result = _to_datetime_delta(timedelta)
        expected = DateTimeDelta(days=104250, microseconds=1)
        assert result == expected

    @given(timedelta=sampled_from([_TIMEDELTA_MICROSECONDS, _TIMEDELTA_OVERFLOW]))
    def test_error(self, *, timedelta: dt.timedelta) -> None:
        with raises(
            _ToDateTimeDeltaError, match="Unable to create DateTimeDelta; got .*"
        ):
            _ = _to_datetime_delta(timedelta)
