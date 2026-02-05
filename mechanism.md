# LangConnect Client — 프로젝트 요약

## 1. 개요
- **목적**: PostgreSQL + pgvector 기반 벡터 DB를 관리하는 GUI
- **참고**: langchain-ai/langconnect 기반
- **스택**: Next.js 15, React 19, TypeScript, Python 3.11+, FastAPI, PostgreSQL 16 (pgvector)

## 2. 아키텍처 (3-tier)
- **Frontend (next-connect-ui)**: Next.js, 포트 3000
- **Backend API (langconnect)**: FastAPI, 포트 8080 — 컬렉션/문서/검색/인증 REST API
- **DB**: pgvector/pgvector:pg16 컨테이너, 포트 5432
- **MCP 서버**: stdio 또는 SSE(기본 8765) — AI 어시스턴트용 도구 제공

## 3. 주요 기능
- **컬렉션**: CRUD, 메타데이터, 통계, 일괄 작업
- **문서**: PDF/TXT/MD/DOCX/HTML 업로드, 텍스트 추출·청킹, 드래그앤드롭
- **검색**: 시맨틱(OpenAI 임베딩), 키워드(Full-Text), 하이브리드(가중치 설정)
- **인증**: Supabase JWT + NextAuth.js, httpOnly 쿠키, 리프레시 토큰 자동 갱신
- **MCP**: 9개 이상 도구(search_documents, list_collections, create_collection 등), RAG 프롬프트/리소스

## 4. 디렉터리 구조
- `langconnect/`: FastAPI 앱, API 라우터(auth, collections, documents), DB·서비스 레이어
- `next-connect-ui/`: Next.js 앱, (auth)/(protected) 라우트, API 프록시, 다국어·테마
- `mcpserver/`: MCP 서버(stdio/SSE), 설정 생성·토큰 발급 스크립트
- `init-scripts/`: PostgreSQL 확장 초기화
- `tests/`: API·문서 처리·MCP 단위/통합 테스트

## 5. 실행
- `make build` → `make up`: Docker Compose로 postgres, api, nextjs 기동
- `make mcp`: MCP 설정 생성 (Supabase 토큰 입력)
- `./run_mcp_sse.sh` 또는 `uv run python mcpserver/mcp_sse_server.py`: MCP SSE 서버 실행
- `make down`: 서비스 종료

## 6. 환경 변수 (필수)
- OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY, NEXTAUTH_SECRET, NEXTAUTH_URL, NEXT_PUBLIC_API_URL
- DB: POSTGRES_* (선택, 기본값 있음)

## 7. 보안·인증 흐름
- 브라우저 ↔ NextAuth(JWT) ↔ Supabase Auth
- 리프레시 토큰은 클라이언트에 노출되지 않음, 만료 시 자동 갱신, JWT는 httpOnly 쿠키에 암호화 저장
