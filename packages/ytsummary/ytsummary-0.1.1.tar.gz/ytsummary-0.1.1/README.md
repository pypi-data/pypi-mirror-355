# YTSummary

YouTube 비디오의 자막을 추출하고 요약하는 Python 라이브러리입니다.

## 설치 방법

```bash
pip install ytsummary
```

## 사용 방법

```python
from ytsummary.youtube_utils import extract_video_id, get_transcript
from ytsummary.summarizer import summarize_text

# YouTube URL에서 비디오 ID 추출
video_url = "https://www.youtube.com/watch?v=your_video_id"
video_id = extract_video_id(video_url)

# 자막 가져오기
transcript = get_transcript(video_id)

# 자막 요약하기
summary = summarize_text(transcript)
print(summary)
```

## 주요 기능

- YouTube 비디오 ID 추출
- 자막 추출 (YouTube Transcript API 사용)
- 텍스트 요약

## 의존성

- requests
- beautifulsoup4
- youtube_transcript_api
- transformers
- torch

## 라이선스

MIT License 