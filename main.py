from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    # PDF 파일 타입 검증
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # 파일 크기 제한 (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB")
    
    # 파일 저장 (실제 환경에서는 적절한 저장소에 저장)
    with open(f"uploads/{file.filename}", "wb") as f:
        f.write(contents)
    
    return {
        "message": "PDF uploaded successfully",
        "filename": file.filename,
        "size": len(contents)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
