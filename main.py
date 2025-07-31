from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import glob
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

app = FastAPI()

# 전역 변수로 벡터스토어 저장
vectorstore = None


# 요청 모델 정의
class ChatRequest(BaseModel):
    message: str


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
    global vectorstore

    # PDF 파일 타입 검증
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # 파일 크기 제한 (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max size is 10MB")

    # uploads 디렉토리 생성
    os.makedirs("uploads", exist_ok=True)

    # 파일 저장
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        # PDF 문서 로드 및 분할
        loader = PyMuPDFLoader(file_path)
        docs = loader.load()

        # 텍스트 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        split_documents = text_splitter.split_documents(docs)

        # 임베딩 생성 및 벡터스토어 구축
        embeddings = OpenAIEmbeddings()
        vectorstore = FAISS.from_documents(
            documents=split_documents,
            embedding=embeddings
        )

        return {
            "message": "PDF uploaded and processed successfully",
            "filename": file.filename,
            "size": len(contents),
            "chunks": len(split_documents)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/chat")
async def chat(request: ChatRequest):
    global vectorstore

    # 벡터스토어가 없으면 에러 반환
    if vectorstore is None:
        raise HTTPException(
            status_code=400,
            detail="No PDF uploaded. Please upload a PDF first."
        )

    try:
        # LLM 모델 초기화
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1
        )

        # 검색기 생성
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # 상위 3개 문서 검색
        )

        # RetrievalQA 체인 생성
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        # 질문에 대한 답변 생성
        result = qa_chain.invoke({"query": request.message})

        # 소스 문서 정보 추출
        source_info = []
        for doc in result.get("source_documents", []):
            source_info.append({
                "page": doc.metadata.get("page", "Unknown"),
                "source": doc.metadata.get("source", "Unknown")
            })

        return {
            "answer": result["result"],
            "sources": source_info,
            "query": request.message
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
