"""
YTSummary - 핵심 기능
"""
import re
import logging
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs, unquote
import json
import html
from typing import Tuple, Dict, Optional, List, Any, Union

# 로깅 설정
logger = logging.getLogger(__name__)

def extract_video_id(url: str) -> Optional[str]:
    """
    유튜브 URL에서 비디오 ID를 추출합니다.
    
    Args:
        url: YouTube 비디오 URL
        
    Returns:
        비디오 ID 또는 None (URL이 유효하지 않은 경우)
    """
    # 일반 유튜브 링크 (예: https://www.youtube.com/watch?v=VIDEO_ID)
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
    
    # 짧은 유튜브 링크 (예: https://youtu.be/VIDEO_ID)
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path.lstrip('/')
    
    # 공유 링크 (예: https://www.youtube.com/shorts/VIDEO_ID)
    elif parsed_url.hostname in ('www.youtube.com', 'youtube.com') and parsed_url.path.startswith('/shorts/'):
        return parsed_url.path.split('/')[2]
    
    # 임베디드 링크 (예: https://www.youtube.com/embed/VIDEO_ID)
    elif parsed_url.hostname in ('www.youtube.com', 'youtube.com') and parsed_url.path.startswith('/embed/'):
        return parsed_url.path.split('/')[2]
    
    # ID를 찾지 못함
    return None

def extract_caption_url_from_html(html_content: str) -> Optional[Dict[str, str]]:
    """
    YouTube 페이지 HTML에서 자막 URL을 추출합니다.
    
    Args:
        html_content: YouTube 페이지 HTML 내용
        
    Returns:
        언어 코드를 키로, 자막 URL을 값으로 하는 딕셔너리 또는 None
    """
    try:
        # playerCaptionsTracklistRenderer에서 자막 정보 찾기
        captions_match = re.search(r'"captions":\s*{.*?"playerCaptionsTracklistRenderer":\s*{"captionTracks":\s*\[(.*?)\]', html_content, re.DOTALL)
        if not captions_match:
            logger.warning("자막 정보를 찾을 수 없습니다.")
            return None
        
        captions_data = captions_match.group(1)
        logger.debug(f"자막 데이터: {captions_data[:500]}...")  # 디버깅 목적
        
        # baseUrl 추출
        caption_urls = {}
        for caption_track in re.finditer(r'"baseUrl":\s*"([^"]*)".*?"languageCode":\s*"([^"]*)"', captions_data):
            url = caption_track.group(1)
            lang_code = caption_track.group(2)
            # URL 디코딩 (이스케이프된 문자 처리)
            url = html.unescape(url.replace('\\u0026', '&'))
            caption_urls[lang_code] = url
        
        return caption_urls
    except Exception as e:
        logger.error(f"자막 URL 추출 중 오류: {e}")
        return None

def fetch_transcript_from_url(url: str) -> Optional[str]:
    """
    지정된 URL에서 자막을 가져와 텍스트로 변환합니다.
    
    Args:
        url: 자막 URL
        
    Returns:
        자막 텍스트 또는 None
    """
    try:
        logger.info(f"자막 URL 접근 중: {url[:100]}...")
        response = requests.get(url)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        logger.info(f"받은 콘텐츠 타입: {content_type}")
        
        # 응답 내용 확인 (디버깅용)
        content_preview = response.text[:200] if response.text else "빈 응답"
        logger.info(f"응답 내용 미리보기: {content_preview}")
        
        if 'text/xml' in content_type or '<transcript>' in response.text or '<timedtext>' in response.text:
            # XML 형식 자막 처리
            try:
                root = ET.fromstring(response.text)
                transcript_lines = []
                
                # 일반적인 YouTube XML 형식 시도
                for elem in root.findall('.//text'):
                    if elem.text:
                        transcript_lines.append(elem.text.strip())
                
                # TTML 형식 시도
                if not transcript_lines:
                    for elem in root.findall('.//{http://www.w3.org/ns/ttml}p'):
                        text = ''.join(elem.itertext()).strip()
                        if text:
                            transcript_lines.append(text)
                
                if transcript_lines:
                    return ' '.join(transcript_lines)
                else:
                    logger.warning(f"XML에서 텍스트 요소를 찾을 수 없습니다. XML 구조: {response.text[:500]}")
            except ET.ParseError as e:
                logger.warning(f"XML 파싱 오류: {e}. 텍스트로 처리 시도합니다.")
        
        # JSON 형식 처리 시도
        if 'application/json' in content_type or response.text.strip().startswith('{'):
            try:
                data = response.json()
                transcript_lines = []
                
                # 여러 JSON 구조 시도
                if 'events' in data:
                    for item in data.get('events', []):
                        if 'segs' in item:
                            for seg in item['segs']:
                                if 'utf8' in seg:
                                    transcript_lines.append(seg['utf8'])
                elif 'actions' in data:
                    for action in data.get('actions', []):
                        if 'updateEngagementPanelAction' in action:
                            content = action['updateEngagementPanelAction'].get('content', {})
                            if 'transcriptRenderer' in content:
                                for item in content['transcriptRenderer'].get('body', {}).get('transcriptBodyRenderer', {}).get('cueGroups', []):
                                    for cue in item.get('transcriptCueGroupRenderer', {}).get('cues', []):
                                        text = cue.get('transcriptCueRenderer', {}).get('cue', {}).get('simpleText')
                                        if text:
                                            transcript_lines.append(text)
                
                if transcript_lines:
                    return ' '.join(transcript_lines)
                else:
                    logger.warning(f"JSON에서 자막 텍스트를 찾을 수 없습니다. JSON 구조: {json.dumps(data)[:500]}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 파싱 실패: {e}. 텍스트로 시도합니다.")
        
        # 직접 텍스트 처리 시도
        if 'text/plain' in content_type or not content_type:
            lines = response.text.splitlines()
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            if non_empty_lines:
                return ' '.join(non_empty_lines)
        
        # 마지막 수단: 응답 자체를 반환
        return response.text if response.text.strip() else None
    except Exception as e:
        logger.error(f"자막 URL에서 자막 가져오기 실패: {e}", exc_info=True)
        return None

def get_video_transcript(video_id: str, preferred_languages: Optional[List[str]] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    비디오 ID로 자막을 추출합니다.
    
    Args:
        video_id: YouTube 비디오 ID
        preferred_languages: 선호하는 언어 코드 리스트 (예: ['ko', 'en'])
        
    Returns:
        (자막 텍스트, 언어 코드) 또는 (None, None)
    """
    if not preferred_languages:
        preferred_languages = ['ko', 'en']  # 기본값: 한국어 우선, 영어 차선
    
    logger.info(f"비디오 ID '{video_id}'의 자막 추출 중...")
    transcript_text = None
    used_language = None
    
    try:
        # 직접 HTML에서 자막 URL 추출 시도
        try:
            # YouTube 페이지 로드
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'
            }
            response = requests.get(f"https://www.youtube.com/watch?v={video_id}", headers=headers)
            
            # 자막 URL 추출
            caption_urls = extract_caption_url_from_html(response.text)
            if caption_urls:
                logger.info(f"발견된 자막 언어: {list(caption_urls.keys())}")
                
                # 선호 언어 순으로 자막 추출 시도
                for lang in preferred_languages:
                    url = None
                    # 정확한 일치 시도
                    if lang in caption_urls:
                        url = caption_urls[lang]
                    # 부분 일치 시도 (ko가 없어도 ko-KR이 있을 수 있음)
                    else:
                        for key in caption_urls.keys():
                            if key.startswith(lang + "-") or key.startswith(lang):
                                url = caption_urls[key]
                                break
                    
                    if url:
                        transcript_text = fetch_transcript_from_url(url)
                        if transcript_text:
                            used_language = lang
                            logger.info(f"자막 URL에서 {lang} 자막을 가져왔습니다.")
                            break
            else:
                logger.warning("HTML에서 자막 URL을 찾을 수 없습니다.")
        except Exception as e:
            logger.error(f"HTML 자막 추출 시도 중 오류: {e}")
                
        # 결과 출력
        if transcript_text:
            logger.info(f"자막 내용 (일부): {transcript_text[:200]}...")  # 자막의 첫 200자만 출력 (디버깅용)
        else:
            logger.warning(f"비디오 ID '{video_id}'에 대해 자막을 찾을 수 없습니다.")
    except Exception as e:
        logger.error(f"자막 추출 중 예외 발생: {e}")
    
    return (transcript_text, used_language) if transcript_text else (None, None)

def get_video_info(video_id: str) -> Optional[Dict[str, Any]]:
    """
    YouTube API 키 없이 YouTube 비디오 정보를 가져옵니다.
    웹 페이지를 스크래핑하여 정보를 추출합니다.
    
    Args:
        video_id: YouTube 비디오 ID
        
    Returns:
        비디오 정보 딕셔너리 또는 None
    """
    try:
        # User-Agent 설정 (YouTube가 일부 요청을 차단할 수 있음)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        
        # 페이지 내용 가져오기
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(video_url, headers=headers)
        html_content = response.text
        
        # 1. 비디오 제목 추출
        title_match = re.search(r'<title>(.*?) - YouTube</title>', html_content)
        if not title_match:
            title_match = re.search(r'"title":"(.*?)"', html_content)
        title = title_match.group(1) if title_match else "알 수 없는 제목"
        title = html.unescape(title)
        
        # 2. 채널 정보 추출
        channel_id_match = re.search(r'"channelId":"(.*?)"', html_content)
        channel_id = channel_id_match.group(1) if channel_id_match else None
        
        channel_title_match = re.search(r'"ownerChannelName":"(.*?)"', html_content)
        if not channel_title_match:
            channel_title_match = re.search(r'"author":"(.*?)"', html_content)
        channel_title = channel_title_match.group(1) if channel_title_match else "알 수 없는 채널"
        
        # 3. 설명 추출
        description_match = re.search(r'"shortDescription":"(.*?)"', html_content)
        if not description_match:
            description_match = re.search(r'"description":{"simpleText":"(.*?)"}', html_content)
        description = description_match.group(1) if description_match else ""
        description = html.unescape(description).replace('\\n', '\n')
        
        # 4. 업로드 날짜 추출
        published_match = re.search(r'"publishDate":"(.*?)"', html_content)
        published_at = published_match.group(1) if published_match else None
        
        # 5. 통계 정보 추출
        view_count_match = re.search(r'"viewCount":"(.*?)"', html_content)
        view_count = view_count_match.group(1) if view_count_match else None
        
        like_count_match = re.search(r'"likeCount":"(.*?)"', html_content)
        like_count = like_count_match.group(1) if like_count_match else None
        
        # 6. 비디오 길이 추출
        length_match = re.search(r'"lengthSeconds":"(.*?)"', html_content)
        length_seconds = length_match.group(1) if length_match else None
        
        # 7. JSON 데이터 추출 시도 (더 신뢰할 수 있는 방법)
        json_data = None
        script_tag_match = re.search(r'<script[^>]*>var ytInitialPlayerResponse\s*=\s*(\{.*?\});', html_content, re.DOTALL)
        if script_tag_match:
            try:
                json_data = json.loads(script_tag_match.group(1))
                video_details = json_data.get('videoDetails', {})
                
                # JSON에서 더 정확한 정보 업데이트
                if video_details:
                    title = video_details.get('title', title)
                    channel_id = video_details.get('channelId', channel_id)
                    channel_title = video_details.get('author', channel_title)
                    description = video_details.get('shortDescription', description)
                    view_count = video_details.get('viewCount', view_count)
                    length_seconds = video_details.get('lengthSeconds', length_seconds)
            except json.JSONDecodeError:
                logger.warning("JSON 데이터 파싱 실패")
        
        # 결과 반환
        return {
            "type": "video",
            "id": video_id,
            "title": title,
            "description": description,
            "channel_id": channel_id,
            "channel_title": channel_title,
            "published_at": published_at,
            "duration": length_seconds,
            "view_count": view_count,
            "like_count": like_count
        }
    
    except Exception as e:
        logger.error(f"비디오 정보 가져오기 실패: {str(e)}", exc_info=True)
        return None

async def get_transcript(video_id: str, languages: List[str] = None) -> Optional[str]:
    """
    유튜브 비디오 ID로부터 자막 또는 비디오 정보를 가져옵니다.
    
    Args:
        video_id: YouTube 비디오 ID
        languages: 선호하는 언어 코드 리스트 (예: ['ko', 'en'])
        
    Returns:
        자막 텍스트 또는 비디오 정보 요약 또는 None
    """
    if languages is None:
        languages = ['ko', 'en']
        
    try:
        # 비디오 정보 가져오기
        video_info = get_video_info(video_id)
        video_title = video_info.get('title', '알 수 없는 제목') if video_info else '알 수 없는 제목'
        channel_title = video_info.get('channel_title', '알 수 없는 채널') if video_info else '알 수 없는 채널'
        description = video_info.get('description', '') if video_info else ''
        view_count = video_info.get('view_count', '0') if video_info else '0'
        
        # 자막 가져오기
        transcript_text, used_language = get_video_transcript(video_id, preferred_languages=languages)
        
        if transcript_text:
            return f"제목: {video_title}\n채널: {channel_title}\n조회수: {view_count}\n\n{transcript_text}"
        else:
            logger.warning(f"비디오 ID {video_id}에 대한 자막을 찾을 수 없습니다.")
            # 자막 대신 제목과 설명 정보 제공
            info_summary = f"제목: {video_title}\n채널: {channel_title}\n조회수: {view_count}\n\n설명:\n{description}"
            logger.info("자막 대신 비디오 정보 요약을 제공합니다.")
            return info_summary
        
    except Exception as e:
        logger.error(f"자막 가져오기 실패: {str(e)}", exc_info=True)
        return "영상 정보를 가져오는 데 실패했습니다. 다시 시도해주세요." 