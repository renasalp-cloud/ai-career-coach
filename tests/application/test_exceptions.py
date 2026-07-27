import unittest

from app.application import (
    AnalysisExecutionError,
    ApplicationError,
    CVProcessingError,
    InvalidCVSourceError,
    RequirementProcessingError,
)


APPLICATION_EXCEPTIONS = (
    InvalidCVSourceError,
    CVProcessingError,
    RequirementProcessingError,
    AnalysisExecutionError,
)


class ApplicationExceptionTest(unittest.TestCase):
    def test_specific_exceptions_subclass_application_error(self) -> None:
        for exception_type in APPLICATION_EXCEPTIONS:
            with self.subTest(exception_type=exception_type):
                self.assertTrue(issubclass(exception_type, ApplicationError))

    def test_exceptions_preserve_a_chained_cause(self) -> None:
        cause = ValueError("underlying failure")

        for exception_type in (ApplicationError, *APPLICATION_EXCEPTIONS):
            with self.subTest(exception_type=exception_type):
                try:
                    raise exception_type("application failure") from cause
                except exception_type as error:
                    self.assertIs(error.__cause__, cause)

    def test_exceptions_have_no_http_specific_fields(self) -> None:
        for exception_type in (ApplicationError, *APPLICATION_EXCEPTIONS):
            with self.subTest(exception_type=exception_type):
                error = exception_type("application failure")

                self.assertFalse(hasattr(error, "status_code"))
                self.assertFalse(hasattr(error, "detail"))


if __name__ == "__main__":
    unittest.main()
