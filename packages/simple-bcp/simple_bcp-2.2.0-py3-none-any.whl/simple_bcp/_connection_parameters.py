import sys
from datetime import timedelta
from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints, field_validator


class MsSqlDatabaseParameters(BaseModel):
    server_hostname: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    port: Annotated[int, Field(gt=0, lt=2**16)] = 1433
    username: str
    password: str
    trust_server_certificate: bool = False
    database_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = Field(
        default=None, description="database name. defaults to the user's default database name"
    )
    login_timeout: None | timedelta = Field(
        default=timedelta(seconds=15),
        description="Timeout for connecting to the sql server. "
        "Defaults to bcp default - 15 seconds. "
        "Must be an integer number of seconds, between 1 and 65534 (inclusive). "
        "Pass `None` to specify no timeout",
    )

    @field_validator("login_timeout")
    @classmethod
    def validate_login_timeout(cls, v: Any):
        if isinstance(v, timedelta):
            seconds = v.total_seconds()
            if int(seconds) != seconds:
                raise ValueError("`login_timeout` must be an integer number of seconds")
            if not (0 < seconds <= 65534):
                raise ValueError("`login_timeout` must be between 1 and 65534 seconds")
        return v

    @property
    def _login_timeout_command_value(self) -> str:
        if self.login_timeout is None:
            return "0"
        else:
            return str(int(self.login_timeout.total_seconds()))

    @property
    def command_options(self) -> dict[str, str | None]:
        options: dict[str, str | None] = {
            "-S": f"{self.server_hostname},{self.port}",
            "-U": self.username,
            "-P": self.password,
            "-l": self._login_timeout_command_value,
        }

        if sys.platform == "linux" and self.trust_server_certificate:
            options["-u"] = None  # trust server certificate, available only on linux

        if self.database_name is not None:
            options["-d"] = self.database_name

        return options
