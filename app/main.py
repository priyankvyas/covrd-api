# app/main.py
from fastapi import FastAPI

app = FastAPI(
    title="Covrd API",
    description="AI-Enhanced Meal Planning Platform API",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Welcome to Covrd API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)