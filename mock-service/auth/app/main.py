from app.security import issue_token, settings, verify_token
from fastapi import FastAPI, Form, Header, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="Local Dev OAuth 2.0 Service")


@app.post("/auth/oauth/v2/token")
def token(
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
):
    if grant_type != "client_credentials":
        raise HTTPException(status_code=400, detail="unsupported_grant_type")
    if client_id != settings.client_id or client_secret != settings.client_secret:
        raise HTTPException(status_code=401, detail="invalid_client")
    return issue_token(client_id)


@app.get("/introspect")
def introspect(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        return JSONResponse(status_code=401, content={"detail": "missing_bearer_token"})
    claims = verify_token(authorization.split(" ", 1)[1])
    if claims is None:
        return JSONResponse(status_code=401, content={"detail": "invalid_or_expired_token"})
    return {"active": True, "sub": claims["sub"], "scope": claims.get("scope")}


@app.get("/health")
def health():
    return {"status": "ok"}
