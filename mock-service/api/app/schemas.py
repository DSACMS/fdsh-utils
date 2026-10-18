from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PreviousName(StrictModel):
    personGivenName: str = Field(min_length=1, max_length=30)
    personMiddleName: str | None = Field(default=None, min_length=1, max_length=30)
    personSurName: str = Field(min_length=1, max_length=30)


class StandardIdentityVerificationRequest(StrictModel):
    personSocialSecurityNumber: str | None = Field(default=None, min_length=4, max_length=9)
    personGivenName: str = Field(min_length=1, max_length=30)
    personMiddleName: str | None = Field(default=None, min_length=1, max_length=30)
    personSurName: str = Field(min_length=1, max_length=30)
    previousNames: list[PreviousName] | None = Field(default=None, min_length=1, max_length=5)
    personBirthDate: date
    asOfDate: date
    termsAcceptedIndicator: Literal[True]

    @field_validator("personSocialSecurityNumber")
    @classmethod
    def validate_ssn(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if len(value) == 4 and value != "0000" and value.isdigit():
            return value
        if len(value) == 9 and value.isdigit() and not value.startswith(("000", "666", "9")):
            return value
        raise ValueError("personSocialSecurityNumber must be four digits or a valid nine-digit SSN")


class SsnOnlyVerificationRequest(StrictModel):
    personSocialSecurityNumber: str = Field(pattern=r"^[0-9]{9}$")
    asOfDate: date
    termsAcceptedIndicator: Literal[True]


NscRequest = StandardIdentityVerificationRequest


class NscRequestEnvelope(StrictModel):
    nscRequest: StandardIdentityVerificationRequest | SsnOnlyVerificationRequest


class ResponseMetadata(StrictModel):
    responseCode: str
    responseText: str
    tdsResponseText: str | None = None


class TransactionDetails(StrictModel):
    transactionId: str = Field(pattern=r"^[0-9]{9,15}$")
    orderId: str = Field(pattern=r"^[0-9]{9,15}$")
    transactionStatusCode: Literal["CNF", "UCF"]
    transactionFee: str = Field(pattern=r"^[0-9]+\.[0-9]{2}$")
    salesTax: str = Field(pattern=r"^[0-9]+\.[0-9]{2}$")
    transactionTotal: str = Field(pattern=r"^[0-9]+\.[0-9]{2}$")
    requestedByText: str = Field(min_length=1, max_length=60)
    requestedDateTimeText: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{1,4}$", max_length=24)
    notifiedDateTimeText: str | None = Field(default=None, pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{1,4}$", max_length=24)
    nscHitIndicator: bool


class StudentInfoProvided(StrictModel):
    personGivenName: str = Field(min_length=1, max_length=30)
    personMiddleName: str | None = Field(default=None, min_length=1, max_length=30)
    personSurName: str = Field(min_length=1, max_length=30)
    previousNames: PreviousName | None = None
    personBirthDate: date


class EnrollmentData(StrictModel):
    enrollmentStatusCode: Literal["F", "Q", "H", "L", "Y", "A", "W", "S", "G", "D"]
    termBeginDate: date
    termEndDate: date
    schoolCertifiedOnDate: date
    anticipatedGraduationDate: date | None = None


class EnrollmentDetails(StrictModel):
    officialSchoolName: str = Field(min_length=1, max_length=100)
    schoolCode: str = Field(pattern=r"^[0-9]{6}$")
    branchCode: str = Field(pattern=r"^[0-9]{2}$")
    currentEnrollmentStatusCode: Literal["CC", "CN"]
    enrollmentData: list[EnrollmentData] = Field(min_length=1, max_length=99)


class NscSuccess(StrictModel):
    transactionDetails: TransactionDetails
    studentInfoProvided: StudentInfoProvided | None = None
    enrollmentDetails: list[EnrollmentDetails] | None = Field(default=None, min_length=1, max_length=99)


class NscError(StrictModel):
    responseMetadata: ResponseMetadata


class NscResponse(StrictModel):
    nscResponse: NscSuccess | NscError
