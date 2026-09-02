from app.domain_registry import Domain, get_domain, register_domain
from app.domains.nsc import retrieve as retrieve_nsc
from app.schemas import NscRequestEnvelope
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="FDSH Mock Retrieve API", version="1.0.0")
register_domain(Domain(name="nsc", request_model=NscRequestEnvelope, retrieve=retrieve_nsc))


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


@app.post("/domains/{domain_name}", response_model=dict)
def retrieve_domain(domain_name: str, payload: dict):
    domain = get_domain(domain_name)
    if domain is None:
        return JSONResponse(
            status_code=404,
            content={"error": f"Unsupported domain: {domain_name}"},
        )
    validated_payload = domain.request_model.model_validate(payload)
    return domain.retrieve(validated_payload)


@app.exception_handler(RequestValidationError)
async def validation_error(_request: Request, _exc: RequestValidationError):
    return error_response("ME123456", "Invalid NSC request", 422)


@app.get("/health")
def health():
    return {"status": "ok"}
