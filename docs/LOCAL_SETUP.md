# LangConnect Client — 로컬 실행 가이드

## 1. 사전 요구사항 (필수)

### 1.1 Docker & Docker Compose
- **Docker**: PostgreSQL·FastAPI·Next.js가 컨테이너로 실행됩니다.
- **Docker Compose**: 여러 서비스를 한 번에 띄우는 데 사용합니다.
- 확인: `docker --version`, `docker compose version`

### 1.2 Node.js 20+
- `make build` 시 Next.js 프론트엔드를 빌드할 때 사용합니다.
- 확인: `node -v` (v20 이상)

### 1.3 (선택) Python 3.11+ & UV
- MCP 서버·설정 스크립트(`make mcp`) 실행 시 필요합니다. 로컬에서 웹/API만 쓸 경우 생략 가능.
- 확인: `python3 --version`, `uv --version`

---

## 2. 환경 변수 설정 (`.env`)

프로젝트 루트에 `.env` 파일이 있어야 합니다. 없으면 `.env.example`을 복사한 뒤 아래 값을 채웁니다.

```bash
cp .env.example .env
# .env 를 편집
```

### 2.1 반드시 필요한 값 (일반 실행)

| 변수 | 설명 | 예시 |
|------|------|------|
| `OPENAI_API_KEY` | 임베딩·시맨틱 검색용 OpenAI API 키 | `sk-...` |
| `SUPABASE_URL` | Supabase 프로젝트 URL | `https://xxxx.supabase.co` |
| `SUPABASE_KEY` | Supabase **anon public** 키 | `eyJ...` |
| `NEXTAUTH_SECRET` | NextAuth 세션 암호화용 (아무 랜덤 문자열) | `langconnect-next-server-secret` 또는 새로 생성 |

- **NEXTAUTH_URL**: 로컬 기본값 `http://localhost:3000` 그대로 사용해도 됩니다.
- **NEXT_PUBLIC_API_URL**: 로컬 기본값 `http://localhost:8080` 그대로 사용해도 됩니다.

### 2.1.1 Azure OpenAI로 Chat + Embeddings 둘 다 쓰는 경우

- **Chat(멀티쿼리 등)** 과 **Embeddings(문서 업로드/검색)** 는 Azure에서 보통 **서로 다른 Deployment** 입니다.
- 아래 2개 배포명을 **반드시 분리**해서 설정하세요.

```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://<your-resource>.cognitiveservices.azure.com
AZURE_OPENAI_API_VERSION=2025-04-01-preview
AZURE_OPENAI_API_KEY=...

# Chat 배포명
AZURE_OPENAI_DEPLOYMENT=gpt-5-mini
# Embeddings 배포명
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
```

- `AZURE_OPENAI_API_VERSION`은 Azure 포털/Foundry의 **View code(코드 예제)** 에서 `api-version=` 값으로 확인하는 것이 가장 확실합니다.
- 업로드 시 `DeploymentNotFound`가 나오면 보통 **임베딩 배포가 없거나(또는 이름 불일치)**, endpoint가 다른 리소스를 가리키는 경우입니다.

### 2.2 Supabase 키 얻는 방법
1. [supabase.com](https://supabase.com) 로그인 후 새 프로젝트 생성
2. **Project Settings** → **API**
3. **Project URL** → `SUPABASE_URL`에 복사
4. **Project API keys** 중 **anon public** → `SUPABASE_KEY`에 복사

### 2.3 PostgreSQL (Docker 사용 시)
- `docker-compose`가 DB를 띄우므로 `POSTGRES_*`는 `.env.example` 기본값으로 두면 됩니다.
- 단, **API 컨테이너 안**에서는 호스트가 `postgres`(서비스 이름)로 자동 설정되므로 `.env`의 `POSTGRES_HOST`는 무시됩니다.

### 2.4 테스트 모드 (로그인 없이 API만 쓰고 싶을 때)
- `.env`에 `IS_TESTING=true` 설정
- 이때는 **SUPABASE_URL, SUPABASE_KEY 비워 둬도** API가 동작합니다.
- 인증: Bearer 토큰에 `user1` 또는 `user2`를 넣으면 통과합니다.
- **주의**: Next.js 로그인 화면은 Supabase가 있어야 하므로, 웹 UI 로그인까지 쓰려면 Supabase를 반드시 설정해야 합니다.

---

## 3. 실행 순서

```bash
# 1) 환경 설정
cp .env.example .env
# OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY, NEXTAUTH_SECRET 등 편집

# 2) 빌드 (Next.js 빌드 + Docker 이미지 빌드)
make build

# 3) 서비스 기동 (PostgreSQL, API, Next.js)
make up
```

### 접속 주소
- **프론트(웹 UI)**: http://localhost:3000  
- **API 문서**: http://localhost:8080/docs  
- **헬스 체크**: http://localhost:8080/health  

### 종료
```bash
make down
```

### (선택) MCP 설정 생성
- Claude/Cursor 등에서 MCP로 이 프로젝트를 쓰려면:
```bash
make mcp
# Supabase 로그인 정보 입력 후 생성된 설정을 각 클라이언트에 등록
```

---

## 4. 문제 해결

- **포트 충돌**: 3000, 5432, 8080이 이미 쓰이면 `docker-compose.yml` 또는 사용 중인 앱에서 포트 변경.
- **Next.js 빌드 실패**: `next-connect-ui`에서 `npm install` 후 `npm run build`를 직접 실행해 에러 로그 확인.
- **API 401**: Supabase 설정이 맞는지, 또는 테스트 모드면 Bearer `user1`/`user2` 사용 여부 확인.
- **임베딩 오류**:
  - OpenAI 사용 시: `OPENAI_API_KEY`가 유효한지 확인
  - Azure 사용 시: `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` 배포가 실제로 존재하는지(이름 일치), `AZURE_OPENAI_ENDPOINT`가 올바른 리소스인지 확인
