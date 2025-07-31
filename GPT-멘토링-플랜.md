# RAG 신입 개발자 성장 멘토링 플랜

## 🧭 1. RAG 시스템의 기본 개념 정리 (1~2주차)

### ✅ 신입이 이해해야 할 개념

- LLM의 한계 (context 길이, 최신성 문제)
- RAG의 정의 및 등장 배경
- RAG의 핵심 구성요소:
  1) Query Embedding – 질문을 벡터로 변환
  2) Retrieval – 유사 문서 검색
  3) Generation – 문서 기반 응답 생성

### 🧑‍🏫 멘토 역할

- 개념 퀴즈 출제
  - 예: "RAG에서 chunking을 하는 이유는?"
- LLM 없이 검색 기반 요약 시스템 먼저 만들게 하기

## 🛠️ 2. 간단한 RAG 예제 구현 (3~4주차)

### 🧪 실습 프로젝트

- PDF 하나 업로드 → 질문하면 답하는 RAG 챗봇

### 스택 예시

- LLM: OpenAI GPT-4
- Embedding: OpenAI embedding API (text-embedding-3-small 등)
- Vector DB: FAISS or Chroma
- Framework: FastAPI

### 🎯 실습 포인트

- 문서 chunking
- Embedding 생성 및 저장
- 벡터 검색 구현 (Top-k)
- Prompt Template 설계

### 🧑‍🏫 멘토 역할

- 전체 파이프라인 구조 설계 지도
- 디버깅 실습: 일부 구성 요소를 의도적으로 잘못 설정해두기
- 토론 유도: "어떤 질문에서 실패할까?"

## 🔬 3. 실제 데이터 적용 & 개선 (5~6주차)

### 📌 실전 과제

- 사내 위키 문서 또는 고객 FAQ 기반 RAG 시스템 구축

### 🎯 개선 포인트

- Retrieval 품질 평가 (Precision@k, Recall@k)
- 다양한 Embedding 모델 실험 (e5-base, bge, Cohere, 등)
- Hallucination 방지 및 출처 포함 응답 생성

### 🧑‍🏫 멘토 역할

- 품질 지표 설계와 실험을 직접 하게 유도
- 임베딩 성능 비교 실습 과제 제공
- Prompt 튜닝 실습
  - 예: "출처를 포함해줘", "요약해줘" 등

## 📈 4. 향후 성장 방향

### 🚀 성장 목표 제시

- 성능 개선:
  - Hybrid Retrieval
  - Caching
  - Feedback loop 도입
- LangChain / LlamaIndex 실전 활용
- 보안: 개인정보(PII) 제거, 내부 정보 유출 방지
- 오픈소스 분석 및 기여:
  - Haystack
  - LlamaIndex

## 📌 추가로 제공 가능

- ✅ 멘토링 체크리스트
- ✅ 코드 예제 & 튜토리얼 미션
- ✅ 실전 RAG 시스템 설계 예시
