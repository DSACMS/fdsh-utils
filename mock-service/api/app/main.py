from app.domains.nsc import retrieve as retrieve_nsc
from app.schemas import NscRequestEnvelope
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="FDSH Mock Retrieve API", version="1.0.0")


def error_response(code: str, text: str, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "nscResponse": {
                "responseMetadata": {
                    "responseCode": code,
                    "responseText": text,
                }
            }
        },
    )


@app.post("/mesh/imp1/NationalStudentClearinghouseService", response_model=dict)
def retrieve_nsc_root(payload: NscRequestEnvelope):
    return retrieve_nsc(payload)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, _exc: RequestValidationError):
    return error_response("ME123456", "Invalid NSC request", 422)


@app.get("/health")
def health():
    return {"status": "ok"}
