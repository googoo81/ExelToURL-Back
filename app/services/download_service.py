import requests
import io
import zipfile
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Tuple

def download_single_xml(url: str, timeout: int = 10) -> Tuple[bool, bytes, str]:
    """
    단일 XML 파일을 다운로드합니다.
    
    Args:
        url: 다운로드할 XML 파일의 URL
        timeout: 요청 타임아웃 시간(초)
    
    Returns:
        (성공 여부, 콘텐츠, 오류 메시지)
    """
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return True, response.content, ""
        else:
            return False, b"", f"Failed to download XML. Status code: {response.status_code}"
    except Exception as e:
        return False, b"", f"Error downloading XML: {str(e)}"

def create_zip_from_urls(urls: List[str], worker_count: int = 5) -> Tuple[bool, io.BytesIO, str]:
    """
    여러 URL에서 XML 파일을 다운로드하여 ZIP 파일을 생성합니다.
    
    Args:
        urls: 다운로드할 XML 파일들의 URL 목록
        worker_count: 동시 다운로드 작업자 수
    
    Returns:
        (성공 여부, ZIP 파일 BytesIO 객체, 오류 메시지)
    """
    if not urls:
        return False, io.BytesIO(), "No URLs provided"
    
    # 결과를 저장할 딕셔너리
    results = {}
    
    # ZIP 파일 생성
    memory_file = io.BytesIO()
    
    # 병렬 다운로드를 위한 함수
    def download_job(idx_url):
        idx, url = idx_url
        success, content, error = download_single_xml(url)
        if success:
            filename = url.split('/')[-1]
            if not filename.endswith('.xml'):
                filename = f"file_{idx}.xml"
            return idx, url, success, content, filename, ""
        else:
            return idx, url, False, b"", "", error
    
    # ThreadPoolExecutor로 병렬 다운로드
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        download_results = list(executor.map(download_job, enumerate(urls)))
    
    # 성공 및 실패 카운트
    success_count = 0
    failure_count = 0
    
    # ZIP 파일에 다운로드한 파일 추가
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for idx, url, success, content, filename, error in download_results:
            if success:
                # ZIP에 파일 추가
                zf.writestr(filename, content)
                success_count += 1
            else:
                failure_count += 1
                print(f"Error processing URL {url}: {error}")
    
    # 하나도 성공하지 못한 경우
    if success_count == 0:
        return False, io.BytesIO(), f"Failed to download any XML files. {failure_count} failures."
    
    # 파일 포인터를 처음으로 되돌림
    memory_file.seek(0)
    
    # 일부 실패가 있는 경우에 대한 메시지
    message = ""
    if failure_count > 0:
        message = f"Downloaded {success_count} files. {failure_count} files failed."
    
    return True, memory_file, message

def get_filename_from_url(url: str, default_name: str = "file.xml") -> str:
    """
    URL에서 파일명을 추출합니다.
    
    Args:
        url: 파일 URL
        default_name: 파일명을 추출할 수 없을 때 사용할 기본 이름
    
    Returns:
        파일명
    """
    if not url:
        return default_name
    
    try:
        filename = url.split('/')[-1]
        if not filename or not filename.strip():
            return default_name
        return filename
    except:
        return default_name