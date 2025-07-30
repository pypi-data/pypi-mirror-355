import re

import pytest

from pathvalidate import ErrorReason, ValidationError
from pathvalidate.handler import NullValueHandler, ReservedNameHandler, raise_error


timstamp_regexp = re.compile(r"^\d+\.\d+$")


class Test_raise_error:
    @pytest.mark.parametrize(
        ["exception"],
        [
            [
                ValidationError(
                    description="hoge",
                    reason=ErrorReason.INVALID_CHARACTER,
                )
            ],
            [
                ValidationError(
                    description="foo",
                    reason=ErrorReason.INVALID_AFTER_SANITIZE,
                )
            ],
        ],
    )
    def test_normal(self, exception):
        with pytest.raises(ValidationError) as e:
            raise_error(exception)
        assert exception == e.value


class Test_NullValueHandler:
    @pytest.mark.parametrize(
        ["exception"],
        [
            [
                ValidationError(
                    description="hoge",
                    reason=ErrorReason.INVALID_CHARACTER,
                )
            ],
            [
                ValidationError(
                    description="foo",
                    reason=ErrorReason.INVALID_AFTER_SANITIZE,
                )
            ],
        ],
    )
    def test_return_null_string(self, exception):
        assert NullValueHandler.return_null_string(exception) == ""

    @pytest.mark.parametrize(
        ["exception"],
        [
            [
                ValidationError(
                    description="hoge",
                    reason=ErrorReason.INVALID_CHARACTER,
                )
            ],
            [
                ValidationError(
                    description="foo",
                    reason=ErrorReason.INVALID_AFTER_SANITIZE,
                )
            ],
        ],
    )
    def test_return_timestamp(self, exception):
        assert timstamp_regexp.search(NullValueHandler.return_timestamp(exception)) is not None


class Test_ReservedNameHandler:
    @pytest.mark.parametrize(
        ["exception", "expected"],
        [
            [
                ValidationError(
                    description="not reusable reserved name",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=False,
                    reserved_name="hoge",
                ),
                "_hoge",
            ],
            [
                ValidationError(
                    description="do nothing to reusable reserved name",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=True,
                    reserved_name="hoge",
                ),
                "hoge",
            ],
            [
                ValidationError(
                    description="do nothing to dot",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=False,
                    reserved_name=".",
                ),
                ".",
            ],
            [
                ValidationError(
                    description="do nothing to double dot",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=False,
                    reserved_name="..",
                ),
                "..",
            ],
        ],
    )
    def test_add_leading_underscore(self, exception, expected):
        assert ReservedNameHandler.add_leading_underscore(exception) == expected

    @pytest.mark.parametrize(
        ["exception", "expected"],
        [
            [
                ValidationError(
                    description="not reusable reserved name",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=False,
                    reserved_name="hoge",
                ),
                "hoge_",
            ],
            [
                ValidationError(
                    description="do nothing to reusable reserved name",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=True,
                    reserved_name="hoge",
                ),
                "hoge",
            ],
            [
                ValidationError(
                    description="do nothing to dot",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=False,
                    reserved_name=".",
                ),
                ".",
            ],
            [
                ValidationError(
                    description="do nothing to double dot",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=False,
                    reserved_name="..",
                ),
                "..",
            ],
        ],
    )
    def test_add_trailing_underscore(self, exception, expected):
        assert ReservedNameHandler.add_trailing_underscore(exception) == expected

    @pytest.mark.parametrize(
        ["exception", "expected"],
        [
            [
                ValidationError(
                    description="not reusable reserved name",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=False,
                    reserved_name="hoge",
                ),
                "hoge",
            ],
            [
                ValidationError(
                    description="reusable reserved name",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=True,
                    reserved_name="hoge",
                ),
                "hoge",
            ],
            [
                ValidationError(
                    description="dot",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=False,
                    reserved_name=".",
                ),
                ".",
            ],
            [
                ValidationError(
                    description="double dot",
                    reason=ErrorReason.RESERVED_NAME,
                    reusable_name=False,
                    reserved_name="..",
                ),
                "..",
            ],
        ],
    )
    def test_as_is(self, exception, expected):
        assert ReservedNameHandler.as_is(exception) == expected
