# LangConnect Client — 문제 해결

## MCP Inspector Connect 시 500 에러

### 현상
- MCP Inspector에서 Transport **SSE**, URL `http://localhost:8765/sse` 로 **Connect** 시 500 에러 발생

### 원인 (직접 확인된 로그)
서버 터미널(`./run_mcp_sse.sh` 실행 중인 창)에 다음 예외가 찍힙니다.

```
ERROR:    Exception in ASGI application
...
  File ".../mcp/server/sse.py", line 202, in handle_post_message
    await writer.send(session_message)
  ...
anyio.ClosedResourceError
```

- **GET /sse** 는 200으로 정상 응답하고, `event: endpoint` 로 `session_id` 를 내려줌.
- 클라이언트(Inspector)가 **POST /messages/?session_id=...** 로 요청을 보내면 서버는 **202 Accepted** 를 반환한 뒤, 응답 본문을 **같은 SSE 스트림**으로 보내려 함.
- 이때 **해당 SSE 스트림이 이미 닫혀 있으면** `writer.send()` 에서 `anyio.ClosedResourceError` 가 발생하고, 이 예외가 처리되지 않아 **500** 이 반환됨.

즉, **Inspector가 GET /sse 연결을 너무 일찍 끊거나, POST와 SSE를 같은 세션으로 유지하지 않을 때** 발생하는 MCP Python SDK(FastMCP 하부) 동작입니다.

### 대응 방법

1. **Inspector 쪽**
   - URL은 반드시 **`http://localhost:8765/sse`** (끝에 `/sse` 포함).
   - 브라우저/Inspector를 최신으로 업데이트 후 다시 시도.
   - (가능하다면) SSE 연결을 유지한 채로 POST를 보내는 옵션이 있는지 확인.

2. **우회: stdio로 도구 테스트**
   - MCP 서버는 **stdio** 로도 동작합니다. Inspector에서 transport를 **stdio** 로 두고,  
     명령을 `uv run python mcpserver/mcp_server.py` (또는 `./run_mcp_server.sh` 의 실행 경로)로 설정해 연결해 보세요.

3. **패키지 업그레이드**
   - `mcp` / `fastmcp` 최신 버전으로 올리면 해당 예외를 처리하는지 확인할 수 있습니다.
   ```bash
   uv pip install -U mcp fastmcp
   ```
   이후 `./run_mcp_sse.sh` 다시 실행 후 Inspector Connect 재시도.

4. **Cursor 등 실제 클라이언트**
   - Cursor의 MCP SSE 연결은 Inspector와 구현이 다를 수 있어, 동일 500이 나오지 않을 수 있습니다.  
     Cursor에서 `mcp_config.json` 으로 SSE URL 설정 후 실제로 도구가 호출되는지 확인해 보는 것도 좋습니다.

### 참고
- 현재 프로젝트: `fastmcp>=0.1.0`, `mcp` 는 fastmcp 의존성(예: 1.9.4).
- MCP 스펙 쪽에서는 SSE 전송이 deprecated 되고 **Streamable HTTP** 로 이전되는 추세이므로, 장기적으로는 해당 전송 방식 지원 여부도 확인이 필요할 수 있습니다.
