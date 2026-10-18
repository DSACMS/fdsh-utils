import os

import jwt
from app.domains.nsc import retrieve as retrieve_nsc
from app.response_codes import mesh_response_metadata
from app.schemas import NscRequestEnvelope
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="FDSH Mock Retrieve API", version="1.0.0")


def error_response(code: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"nscResponse": {"responseMetadata": mesh_response_metadata(code)}},
    )


def authorize(request: Request) -> JSONResponse | None:
    authorization = request.headers.get("Authorization", "")
    if not authorization.lower().startswith("bearer "):
        return error_response("ME110010", 401)
    try:
        claims = jwt.decode(
            authorization.split(" ", 1)[1],
            os.getenv("JWT_SIGNING_KEY", "local-dev-signing-key"),
            algorithms=["HS256"],
        )
    except jwt.PyJWTError:
        return error_response("ME110010", 401)
    if claims.get("scope") != "nsc:read":
        return error_response("ME100005", 403)
    return None


@app.post("/mesh/imp1/NationalStudentClearinghouseService", response_model=dict)
def retrieve_nsc_root(request: Request, payload: NscRequestEnvelope):
    authorization_error = authorize(request)
    if authorization_error is not None:
        return authorization_error
    return retrieve_nsc(payload)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, exc: RequestValidationError):
    field_codes = {
        "personSocialSecurityNumber": "ME110020",
        "personSurName": "ME110030",
        "personGivenName": "ME110040",
        "personMiddleName": "ME110050",
        "personBirthDate": "ME110060",
        "asOfDate": "ME110075",
        "previousNames.personGivenName": "ME120030",
        "previousNames.personSurName": "ME120040",
        "previousNames.personMiddleName": "ME120045",
    }
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", ()) if not isinstance(part, int)]
        if "previousNames" in location:
            name_field = next(
                (field for field in ("personGivenName", "personSurName", "personMiddleName") if field in location),
                None,
            )
            field = f"previousNames.{name_field}" if name_field else ""
        else:
            field = next(
                (field for field in field_codes if field.split(".")[-1] in location),
                "",
            )
        if field:
            return error_response(field_codes[field], 422)
    return error_response("ME007000", 422)


@app.exception_handler(Exception)
async def unexpected_exception(_request: Request, _exc: Exception):
    return error_response("MX009000", 500)


@app.get("/health")
def health():
    return {"status": "ok"}
