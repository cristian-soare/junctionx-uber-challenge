"""Custom exceptions for the application."""

from fastapi import HTTPException, status


class DriverPreferencesNotSetError(HTTPException):
  """Raised when driver has not set working hours preferences."""

  def __init__(self) -> None:
    """Initialize the exception."""
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Driver has not set working hours preferences",
    )


class TimeOutsideWorkingHoursError(HTTPException):
  """Raised when selected time is outside working hours range."""

  def __init__(self) -> None:
    """Initialize the exception."""
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Selected time is outside working hours range",
    )


class CurrentTimeOutsideWorkingHoursError(HTTPException):
  """Raised when current time is outside working hours range."""

  def __init__(self) -> None:
    """Initialize the exception."""
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Current time is outside working hours range",
    )


class TimeNotSelectedError(HTTPException):
  """Raised when driver has not selected a time."""

  def __init__(self) -> None:
    """Initialize the exception."""
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Driver has not selected a time",
    )


class TimeNotSelectedAndNoCurrentTimeError(HTTPException):
  """Raised when driver has not selected a time and no current_time provided."""

  def __init__(self) -> None:
    """Initialize the exception."""
    super().__init__(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Driver has not selected a time and no current_time provided",
    )
