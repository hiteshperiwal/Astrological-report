from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import date, datetime

class BirthRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    dob: str
    tob: str = Field(pattern=r"^\d{2}:\d{2}(:\d{2})?$")
    place: str = ""
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = "Asia/Kolkata"
    forecast_amount: int = Field(default=5, ge=1, le=3650)
    forecast_unit: str = Field(default="years", pattern=r"^(days|months|years)$")
    forecast_granularity: str | None = Field(default=None, pattern=r"^(daily|weekly|monthly|quarterly)$")
    school: str = Field(default="synthesis", pattern=r"^(parashari|jaimini|tajaka|synthesis)$")
    # Backward compatibility with the previous UI/API.
    forecast_years: int | None = Field(default=None, ge=1, le=30)
    forecast_start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    forecast_end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("dob")
    @classmethod
    def valid_dob(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            raise ValueError("dob must be a real calendar date in YYYY-MM-DD format")
        return v

    @field_validator("tob")
    @classmethod
    def valid_tob(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%H:%M:%S" if len(v) == 8 else "%H:%M")
        except (TypeError, ValueError):
            raise ValueError("tob must be a valid 24-hour time, HH:MM or HH:MM:SS")
        return v

    @field_validator("forecast_start_date", "forecast_end_date")
    @classmethod
    def valid_forecast_dates(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                date.fromisoformat(v)
            except (TypeError, ValueError):
                raise ValueError("forecast dates must be real calendar dates in YYYY-MM-DD format")
        return v

    @model_validator(mode="after")
    def ordered_forecast_dates(self):
        if bool(self.forecast_start_date) != bool(self.forecast_end_date):
            raise ValueError("Provide both forecast_start_date and forecast_end_date, or leave both blank")
        if self.forecast_start_date and self.forecast_end_date:
            start = date.fromisoformat(self.forecast_start_date)
            end = date.fromisoformat(self.forecast_end_date)
            if end < start:
                raise ValueError("forecast_end_date must be on or after forecast_start_date")
            if (end - start).days > 10958:
                raise ValueError("Personal forecast date range cannot exceed 30 years")
        unit_limits = {"days": 3650, "months": 360, "years": 30}
        if self.forecast_amount > unit_limits[self.forecast_unit]:
            raise ValueError(f"forecast_amount for {self.forecast_unit} cannot exceed {unit_limits[self.forecast_unit]}")
        return self

    @field_validator("timezone")
    @classmethod
    def valid_tz(cls, v: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            raise ValueError("timezone must be a valid IANA timezone name")
        return v

    @field_validator("forecast_unit")
    @classmethod
    def normalize_unit(cls, v: str) -> str:
        return v.lower()

class MundaneRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    country: str = Field(min_length=1, max_length=120)
    historical_event_types: list[str] = Field(default_factory=list)
    historical_limit: int = Field(default=50, ge=1, le=500)
    near_term_amount: int = Field(default=24, ge=1, le=120)
    near_term_unit: str = Field(default="months", pattern=r"^(days|months|years)$")
    long_term_amount: int = Field(default=10, ge=1, le=50)
    long_term_unit: str = Field(default="years", pattern=r"^(days|months|years)$")
    period_start_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    period_end_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    leader_name: str | None = Field(default=None, max_length=200)
    leader_custom: bool = False
    leader_dob: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    leader_tob: str | None = Field(default=None, pattern=r"^\d{2}:\d{2}(:\d{2})?$")
    leader_place: str | None = Field(default=None, max_length=200)
    leader_latitude: float | None = Field(default=None, ge=-90, le=90)
    leader_longitude: float | None = Field(default=None, ge=-180, le=180)
    leader_timezone: str = "Asia/Kolkata"
    leader_time_status: str = Field(default="unknown", pattern=r"^(verified|reported|approximate|unknown)$")

    @field_validator("country")
    @classmethod
    def clean_country(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("country cannot be blank")
        return value

    @field_validator("period_start_date", "period_end_date", "leader_dob")
    @classmethod
    def valid_mundane_dates(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                date.fromisoformat(v)
            except (TypeError, ValueError):
                raise ValueError("dates must be real calendar dates in YYYY-MM-DD format")
        return v

    @field_validator("leader_tob")
    @classmethod
    def valid_leader_time(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                datetime.strptime(v, "%H:%M:%S" if len(v) == 8 else "%H:%M")
            except (TypeError, ValueError):
                raise ValueError("leader_tob must be a valid 24-hour time, HH:MM or HH:MM:SS")
        return v

    @field_validator("leader_timezone")
    @classmethod
    def valid_leader_tz(cls, v: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError, TypeError):
            raise ValueError("leader_timezone must be a valid IANA timezone name")
        return v

    @model_validator(mode="after")
    def validate_mundane_period_and_custom_leader(self):
        if bool(self.period_start_date) != bool(self.period_end_date):
            raise ValueError("Provide both period_start_date and period_end_date, or leave both blank")
        if self.period_start_date and self.period_end_date:
            start = date.fromisoformat(self.period_start_date)
            end = date.fromisoformat(self.period_end_date)
            if end < start:
                raise ValueError("period_end_date must be on or after period_start_date")
            if (end - start).days > 18263:
                raise ValueError("Mundane forecast date range cannot exceed 50 years")
        near_limits = {"days": 3650, "months": 120, "years": 30}
        long_limits = {"days": 18263, "months": 600, "years": 50}
        if self.near_term_amount > near_limits[self.near_term_unit]:
            raise ValueError(f"near_term_amount for {self.near_term_unit} cannot exceed {near_limits[self.near_term_unit]}")
        if self.long_term_amount > long_limits[self.long_term_unit]:
            raise ValueError(f"long_term_amount for {self.long_term_unit} cannot exceed {long_limits[self.long_term_unit]}")
        if len(self.historical_event_types) > 30 or any(len(x) > 80 for x in self.historical_event_types):
            raise ValueError("Provide at most 30 historical event filters, each 80 characters or fewer")
        if self.leader_custom:
            missing = [name for name, value in {
                "leader_dob": self.leader_dob,
                "leader_place": self.leader_place,
                "leader_latitude": self.leader_latitude,
                "leader_longitude": self.leader_longitude,
            }.items() if value is None or (isinstance(value, str) and not value.strip())]
            if missing:
                raise ValueError("Custom leader requires: " + ", ".join(missing))
        return self

class MuhurtaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    activity: str = Field(pattern=r"^(puja|job_start|property_buy|property_sell|business_start|expense|property_legal|travel|education)$")
    start_date: str
    end_date: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: str = "Asia/Kolkata"
    natal_dob: str | None = None
    natal_tob: str | None = None
    natal_timezone: str | None = None

    @field_validator("start_date", "end_date", "natal_dob")
    @classmethod
    def valid_dates(cls, v: str | None) -> str | None:
        if v is not None:
            try: date.fromisoformat(v)
            except (TypeError, ValueError): raise ValueError("Dates must be real calendar dates in YYYY-MM-DD format")
        return v

    @field_validator("timezone", "natal_timezone")
    @classmethod
    def valid_timezone(cls, v: str | None) -> str | None:
        if v is not None:
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
            try: ZoneInfo(v)
            except (ZoneInfoNotFoundError, ValueError, TypeError): raise ValueError("Timezone must be a valid IANA timezone name")
        return v

    @field_validator("natal_tob")
    @classmethod
    def valid_birth_time(cls, v: str | None) -> str | None:
        if v is not None:
            try: datetime.strptime(v, "%H:%M:%S" if len(v)==8 else "%H:%M")
            except (TypeError, ValueError): raise ValueError("Birth time must be HH:MM or HH:MM:SS")
        return v

    @model_validator(mode="after")
    def validate_period_and_birth_data(self):
        if date.fromisoformat(self.end_date) < date.fromisoformat(self.start_date):
            raise ValueError("end_date must be on or after start_date")
        if (date.fromisoformat(self.end_date)-date.fromisoformat(self.start_date)).days > 90:
            raise ValueError("Muhurta search period cannot exceed 90 days")
        if bool(self.natal_dob) != bool(self.natal_tob):
            raise ValueError("Provide both natal birth date and time for personalization, or leave both blank")
        return self


class LibraryAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    forecast_amount: int = Field(default=5, ge=1, le=365)
    forecast_unit: str = Field(default="years", pattern=r"^(days|months|years)$")
    school: str = Field(default="synthesis", pattern=r"^(parashari|jaimini|tajaka|synthesis)$")

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name cannot be blank")
        return value


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str = Field(max_length=4000)

class PersonalChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=5000)
    birth: BirthRequest
    history: list[ChatMessage] = Field(default_factory=list, max_length=8)

    @field_validator("question")
    @classmethod
    def clean_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question cannot be blank")
        return value
