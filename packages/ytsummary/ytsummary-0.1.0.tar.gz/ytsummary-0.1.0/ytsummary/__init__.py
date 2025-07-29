"""
YTSummary - YouTube 비디오 정보 및 자막 추출 라이브러리
"""

from .youtube_utils import extract_video_id, get_transcript
from .summarizer import summarize_text

__version__ = "0.1.0"
__all__ = ["extract_video_id", "get_transcript", "summarize_text"] 