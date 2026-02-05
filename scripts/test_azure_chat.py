#!/usr/bin/env python3
"""Azure Chat(멀티쿼리용 LLM) 연동만 확인하는 스크립트. .env의 LLM_PROVIDER=azure 설정을 사용합니다."""

import asyncio
import os
import sys
from pathlib import Path

# 프로젝트 루트에서 .env 로드
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
os.chdir(root)

from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = (os.getenv("LLM_PROVIDER") or "openai").lower()
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")


def get_llm():
    """MCP 서버와 동일한 방식으로 LLM 인스턴스 반환."""
    if LLM_PROVIDER == "azure" and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY:
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT.rstrip("/"),
            api_key=AZURE_OPENAI_API_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            deployment_name=AZURE_OPENAI_DEPLOYMENT or "gpt-4o-mini",
            temperature=1,  # 일부 Azure 모델은 0 미지원
        )
    from langchain_openai import ChatOpenAI

    key = os.getenv("OPENAI_API_KEY", "")
    if key:
        return ChatOpenAI(temperature=0, api_key=key)
    return None


async def main():
    print("🔍 Azure Chat(멀티쿼리) 연동 확인 중...")
    print(f"   LLM_PROVIDER={LLM_PROVIDER}")
    print(f"   AZURE_OPENAI_ENDPOINT={AZURE_OPENAI_ENDPOINT or '(비어 있음)'}")
    print(f"   AZURE_OPENAI_DEPLOYMENT={AZURE_OPENAI_DEPLOYMENT or '(기본값 사용)'}")
    print()

    llm = get_llm()
    if llm is None:
        print("❌ LLM 미설정: .env에 OPENAI_API_KEY 또는 (Azure) AZURE_OPENAI_* 를 설정하세요.")
        sys.exit(1)

    # 1) 단순 호출 테스트
    print("1) 단문 응답 테스트...")
    try:
        msg = await llm.ainvoke("한 단어로만 답하세요: OK")
        text = msg.content if hasattr(msg, "content") else str(msg)
        print(f"   응답: {text.strip()}")
        print("   ✅ 단문 호출 성공")
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        sys.exit(1)

    # 2) 멀티쿼리와 동일한 프롬프트 스타일 테스트
    print("\n2) 멀티쿼리 스타일 테스트 (질문 → 여러 쿼리 생성)...")
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import BaseOutputParser

    class LineListOutputParser(BaseOutputParser[list[str]]):
        def parse(self, text: str) -> list[str]:
            lines = [line.strip() for line in text.strip().split("\n")]
            return [line for line in lines if line]

    prompt = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI language model assistant. Your task is to generate 3 to 5 
different versions of the given user question to retrieve relevant documents from a vector 
database. By generating multiple perspectives on the user question, your goal is to help
the user overcome some of the limitations of the distance-based similarity search. 
Provide these alternative questions separated by newlines. Do not number them.
Original question: {question}""",
    )
    parser = LineListOutputParser()
    chain = prompt | llm | parser
    try:
        queries = await chain.ainvoke({"question": "RAG란 무엇인가?"})
        print(f"   생성된 쿼리 수: {len(queries)}")
        for i, q in enumerate(queries, 1):
            print(f"   - {i}. {q[:60]}{'...' if len(q) > 60 else ''}")
        print("   ✅ 멀티쿼리 스타일 호출 성공")
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        sys.exit(1)

    print("\n✅ Azure Chat(멀티쿼리) 연동이 정상입니다.")


if __name__ == "__main__":
    asyncio.run(main())
