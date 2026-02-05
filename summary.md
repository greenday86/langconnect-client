# LangConnect Client — 오늘 작업 요약 (참고용)

나중에 참고할 목적으로, 오늘 수행한 작업·트러블슈팅·자주 묻던 질문·참고 사항을 정리한 문서입니다.

---

## 1. 주요 수정 사항

### 1.1 프로젝트 문서/구조
- **mechanism.md**: 프로젝트 개요, 아키텍처, 디렉터리 구조, 실행 방법, 환경 변수, 보안 흐름 요약
- **docs/LOCAL_SETUP.md**: 로컬 실행 가이드(사전 요구사항, `.env` 설정, Azure OpenAI 사용 시 Chat/Embeddings 배포 분리, 실행 순서, 문제 해결)
- **troubleshoot.md**: MCP Inspector Connect 500 에러 원인(ClosedResourceError) 및 대응 방법

### 1.2 빌드·실행
- **Makefile**: `docker-compose` → `docker compose` (Docker Compose v2 호환)
- **requirements.txt**: `numba>=0.60.0` 추가 — Python 3.11 Docker 빌드 시 llvmlite/numba 호환

### 1.3 Azure OpenAI 연동
- **langconnect/config.py**: `LLM_PROVIDER=azure` 일 때 `AzureOpenAIEmbeddings` 사용 (엔드포인트, API 키, 버전, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`)
- **mcpserver/mcp_server.py**, **mcpserver/mcp_sse_server.py**: `multi_query`에서 Azure일 때 `AzureChatOpenAI` 사용; 일부 Azure 모델(gpt-5-mini 등)은 `temperature=0` 미지원이라 `temperature=1` 로 설정
- **.env.example**: Azure 관련 변수(LLM_PROVIDER, AZURE_OPENAI_* ) 주석으로 문서화
- **.env**: Chat용 `AZURE_OPENAI_DEPLOYMENT`, Embeddings용 `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` 분리

### 1.4 인증·의존성
- **langconnect/auth.py**: `gotrue.types.User` → `supabase_auth.types.User` 우선, 없으면 `gotrue.types.User`, 최후 `Any` 로 fallback (API 컨테이너 `ModuleNotFoundError: No module named 'gotrue'` 해결)

### 1.5 테스트·스크립트 추가
- **scripts/test_azure_chat.py**: Azure Chat(멀티쿼리) 연동만 검증하는 스크립트 — 단문 호출 + 멀티쿼리 스타일 호출; 실행은 `uv run python scripts/test_azure_chat.py`

---

## 2. 트러블슈팅

| 현상 | 원인 | 조치 |
|------|------|------|
| `make build` 시 `docker-compose` not found | Compose v2는 `docker compose`(공백) 사용 | Makefile에서 `docker compose` 로 변경 |
| API 컨테이너 Restarting, `ModuleNotFoundError: No module named 'gotrue'` | supabase-py 2.x에서 auth 타입이 `supabase_auth` 로 분리됨 | `langconnect/auth.py`에서 `supabase_auth.types.User` 우선 import, fallback으로 gotrue/Any |
| Docker API 이미지 빌드 실패 (llvmlite/numba) | Python 3.11 환경에서 구버전 numba/llvmlite 비호환 | `requirements.txt`에 `numba>=0.60.0` 추가 |
| `make mcp` 시 Connection refused (localhost:8080) | API 서버가 떠 있지 않음 | `make up`으로 API 기동 후 `make mcp` 재실행 |
| 문서 업로드 시 `DeploymentNotFound` (404) | Azure에 임베딩 배포가 없거나 이름 불일치 | Azure에서 Embeddings 모델(예: text-embedding-3-small) 배포 후 `.env`에 `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` 설정 |
| Azure Chat 호출 시 `temperature` does not support 0.0 | 해당 Azure 배포 모델이 0 미지원 | MCP 서버·테스트 스크립트에서 Azure 사용 시 `temperature=1` 로 설정 |
| MCP Inspector Connect 시 500 | POST /messages 처리 후 SSE 스트림에 응답 보낼 때 스트림이 이미 닫혀 `anyio.ClosedResourceError` | `troubleshoot.md` 참고 — URL `/sse` 확인, stdio 우회, mcp/fastmcp 업그레이드 시도 |
| `python scripts/test_azure_chat.py` → ModuleNotFoundError: dotenv | 시스템 Python에 python-dotenv 미설치 | `uv run python scripts/test_azure_chat.py` 로 실행 |

---

## 3. 자주 어려워했던 부분 — 질의 응답 요약

- **make mcp 시 입력하는 email은?**  
  Supabase Auth에 등록된 사용자 이메일. 웹 UI `http://localhost:3000/signup`으로 가입한 계정이거나, Supabase 대시보드 Authentication → Users에 있는 계정.

- **docker ps에서 API가 Restarting인 이유?**  
  API 프로세스가 기동 중 크래시를 반복하는 상태. 로그는 `docker logs langconnect-api --tail=200` 으로 확인. (오늘은 `gotrue` import 오류가 원인이었음.)

- **.env에 Azure만 넣고 OPENAI_API_KEY 없이 쓸 수 있나?**  
  가능. `LLM_PROVIDER=azure` 와 `AZURE_OPENAI_*` 변수들을 설정. 단, **Chat** 과 **Embeddings** 는 Azure에서 별도 배포이므로 `AZURE_OPENAI_DEPLOYMENT`(Chat), `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`(Embeddings) 둘 다 설정해야 문서 업로드와 멀티쿼리가 모두 동작함.

- **AZURE_OPENAI_API_VERSION은 어디서 확인?**  
  Azure 포털/Foundry에서 Playground 등 화면의 **View code(코드 예제)** 에서 `api-version=` 값 확인.

- **make mcp는 MCP 서버 기동인가?**  
  아니다. `make mcp`는 MCP **설정 파일(mcp_config.json) 생성** 및 Supabase 로그인으로 **access token 발급·.env 갱신**까지 수행. 서버 기동은 `./run_mcp_server.sh`(stdio) 또는 `./run_mcp_sse.sh`(SSE).

- **run_mcp_server.sh 용도?**  
  stdio 방식 MCP 서버를 기동하는 스크립트. 프로젝트 루트로 이동한 뒤 `uv run python mcpserver/mcp_server.py` 실행.

- **이 프로젝트에서 Supabase 용도?**  
  **인증(Auth) 전용** — 회원가입·로그인·JWT 발급·검증. 문서/벡터 저장은 PostgreSQL(pgvector) 사용.

- **LLM 사용 목적이 문서 업로드(임베딩) 때만?**  
  아니다. (1) **임베딩**: 문서 업로드·검색 시 벡터 생성. (2) **Chat**: MCP `multi_query` 도구에서 질문 → 3~5개 변형 쿼리 생성해 검색 품질 향상.

- **LLM_PROVIDER=azure 가 꼭 필요한가?**  
  Azure를 쓰려면 필요. 이 변수로 OpenAI vs Azure 분기하므로 없으면 기본값 `openai` 로 동작해 Azure 설정이 무시됨.

- **Cursor에서 langconnect-rag-mcp 설정 방법?**  
  `mcpserver/mcp_config.json` 의 `mcpServers.langconnect-rag-mcp` 블록 전체를 Cursor 설정의 MCP JSON에 붙여넣기. `command`/`args` 경로와 `env.SUPABASE_JWT_SECRET`(토큰)을 환경에 맞게 유지.

---

## 4. 기타 참고 사항

- **Chat vs Embeddings (Azure)**  
  Azure OpenAI에서는 Chat용 배포와 Embeddings용 배포가 보통 별도. 문서 업로드/시맨틱 검색은 Embeddings 배포, 멀티쿼리 생성은 Chat 배포 사용.

- **관련 문서 위치**  
  - 프로젝트 요약: `mechanism.md`  
  - 로컬 실행: `docs/LOCAL_SETUP.md`  
  - 문제 해결: `troubleshoot.md`  
  - 이 요약: `summary.md`

- **MCP Inspector 500**  
  서버 로그에 `ClosedResourceError` 가 찍히면, Inspector가 SSE 연결을 일찍 끊는 쪽 이슈 가능. stdio로 연결하거나 Cursor에서 실제 도구 호출이 되는지 확인하는 것이 좋음.

- **토큰 만료**  
  Supabase JWT(SUPABASE_JWT_SECRET)는 약 1시간 후 만료. MCP/API 호출이 401이 되면 `make mcp` 로 다시 로그인해 토큰 갱신 후 `.env`/mcp_config 반영.

- **테스트 스크립트 실행**  
  `scripts/test_azure_chat.py` 등은 의존성이 프로젝트 venv에 있으므로 `uv run python scripts/test_azure_chat.py` 로 실행.
