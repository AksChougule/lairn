from fastapi import FastAPI

app = FastAPI(title="Liarn API")

@app.get("/health")
def health():
    return {"status": "ok"}
