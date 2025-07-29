import os
import logging
import openai
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

# OpenAI API 키 설정 (직접 설정)
API_KEY = "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"

# OpenAI API 클라이언트 v1 버전용 요약 함수
async def summarize_text(text, max_length=4000):
    """텍스트를 요약합니다 (OpenAI API v1 사용)."""
    try:
        # 텍스트가 너무 길면 자르기 (OpenAI API 토큰 제한 때문)
        if len(text) > max_length:
            text = text[:max_length]
        
        # OpenAI API v1을 사용하여 요약 (gpt-4o-mini 모델 사용)
        client = openai.OpenAI(api_key=API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "당신은 텍스트를 간결하고 명확하게 요약하는 도우미입니다. 주어진 유튜브 영상의 자막을 읽고 핵심 내용을 요약해주세요."},
                {"role": "user", "content": f"다음 유튜브 영상의 자막을 요약해주세요:\n\n{text}"}
            ],
            max_tokens=500,
            temperature=0.3,
        )
        
        # 요약 추출
        summary = response.choices[0].message.content.strip()
        return summary
    
    except Exception as e:
        logger.error(f"텍스트 요약 실패: {str(e)}")
        return "요약에 실패했습니다. 다시 시도해주세요." 