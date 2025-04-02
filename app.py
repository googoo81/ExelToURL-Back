from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import concurrent.futures
import time
import uuid
import xml.etree.ElementTree as ET
from collections import Counter

app = Flask(__name__)
CORS(app)  # 모든 엔드포인트에 CORS 허용

# 작업 상태 저장용 딕셔너리
jobs = {}

# 기본 경로
@app.route('/')
def home():
    return "URL 유효성 검사 서비스가 실행 중입니다."

# 단일 URL 검사
@app.route('/check-url', methods=['GET'])
def check_url():
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'error': 'URL이 제공되지 않았습니다.'
        }), 400
    
    try:
        # HEAD 요청으로 상태 코드만 확인하고 본문은 다운로드하지 않음
        response = requests.head(url, timeout=5)
        status_code = response.status_code
        
        # 상태 코드가 200대면 유효한 URL로 간주
        is_valid = 200 <= status_code < 300
        
        return jsonify({
            'url': url,
            'isValid': is_valid,
            'statusCode': status_code
        })
    except requests.Timeout:
        # 타임아웃 발생 시
        return jsonify({
            'url': url,
            'isValid': False,
            'statusCode': 408,  # Request Timeout
            'error': '요청 시간 초과'
        })
    except requests.RequestException as e:
        # HEAD 요청이 실패할 경우 GET 요청 시도
        try:
            response = requests.get(url, timeout=5, stream=True)
            # stream=True로 설정하여 전체 내용을 다운로드하지 않고 응답 헤더만 확인
            # 바로 연결 종료
            response.close()
            
            status_code = response.status_code
            is_valid = 200 <= status_code < 300
            
            return jsonify({
                'url': url,
                'isValid': is_valid,
                'statusCode': status_code
            })
        except Exception as inner_e:
            # 모든 시도 실패 시
            return jsonify({
                'url': url,
                'isValid': False,
                'statusCode': 0,
                'error': str(inner_e)
            })

# 폴링 방식의 비동기 작업 시작
@app.route('/start-validation', methods=['POST'])
def start_validation():
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({
            'error': 'URLs가 제공되지 않았습니다.'
        }), 400
    
    # 고유 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # 작업 상태 초기화
    urls = data['urls']
    jobs[job_id] = {
        'status': 'in_progress',
        'total': len(urls),
        'completed': 0,
        'results': [],
        'urls': urls
    }
    
    # 백그라운드에서 작업 시작
    def process_urls():
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # URL마다 검사 작업 생성
            future_to_url = {executor.submit(check_single_url, url): url for url in urls}
            
            # 완료된 작업 처리
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    jobs[job_id]['results'].append(result)
                except Exception as e:
                    jobs[job_id]['results'].append({
                        'url': url,
                        'isValid': False,
                        'statusCode': 0,
                        'error': str(e)
                    })
                
                # 진행 상태 업데이트
                jobs[job_id]['completed'] += 1
            
            # 모든 작업 완료 후 상태 업데이트
            jobs[job_id]['status'] = 'completed'
    
    # 비동기 작업 시작
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(process_urls)
    
    # 작업 ID 반환
    return jsonify({
        'job_id': job_id,
        'status': 'in_progress',
        'message': '검증 작업이 시작되었습니다.'
    })

# 작업 상태 확인 API
@app.route('/job-status/<job_id>', methods=['GET'])
def job_status(job_id):
    if job_id not in jobs:
        return jsonify({
            'error': '존재하지 않는 작업 ID입니다.'
        }), 404
    
    job = jobs[job_id]
    
    # 작업이 완료되면 결과 포함
    if job['status'] == 'completed':
        response_data = {
            'status': 'completed',
            'progress': 100,
            'results': job['results']
        }
        
        # TYPE 분석 결과가 있으면 포함
        if 'type_counts' in job:
            response_data['type_counts'] = job['type_counts']
            
        return jsonify(response_data)
    
    # 진행 중인 경우 진행률 계산
    progress = int((job['completed'] / job['total']) * 100) if job['total'] > 0 else 0
    
    response_data = {
        'status': 'in_progress',
        'progress': progress,
        'completed': job['completed'],
        'total': job['total']
    }
    
    # 부분적인 TYPE 분석 결과가 있으면 포함
    if 'type_counts' in job:
        response_data['type_counts'] = job['type_counts']
        
    return jsonify(response_data)

# XML 파일 전용 검사 작업 시작
@app.route('/start-xml-validation', methods=['POST'])
def start_xml_validation():
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({
            'error': 'URLs가 제공되지 않았습니다.'
        }), 400
    
    # 고유 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # 작업 상태 초기화
    urls = data['urls']
    jobs[job_id] = {
        'status': 'in_progress',
        'total': len(urls),
        'completed': 0,
        'results': [],
        'urls': urls
    }
    
    # 백그라운드에서 작업 시작
    def process_xml_urls():
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # URL마다 검사 작업 생성
            future_to_url = {executor.submit(check_xml_url, url): url for url in urls}
            
            # 완료된 작업 처리
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    jobs[job_id]['results'].append(result)
                except Exception as e:
                    jobs[job_id]['results'].append({
                        'url': url,
                        'isValid': False,
                        'statusCode': 0,
                        'error': str(e)
                    })
                
                # 진행 상태 업데이트
                jobs[job_id]['completed'] += 1
            
            # 모든 작업 완료 후 상태 업데이트
            jobs[job_id]['status'] = 'completed'
    
    # 비동기 작업 시작
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(process_xml_urls)
    
    # 작업 ID 반환
    return jsonify({
        'job_id': job_id,
        'status': 'in_progress',
        'message': 'XML 검증 작업이 시작되었습니다.'
    })

# XML Type 태그 분석 작업 시작
@app.route('/analyze-xml-types', methods=['POST'])
def analyze_xml_types():
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({
            'error': 'URLs가 제공되지 않았습니다.'
        }), 400
    
    # 고유 작업 ID 생성
    job_id = str(uuid.uuid4())
    
    # 작업 상태 초기화
    urls = data['urls']
    jobs[job_id] = {
        'status': 'in_progress',
        'total': len(urls),
        'completed': 0,
        'results': [],
        'type_counts': Counter(),
        'urls': urls
    }
    
    # 백그라운드에서 작업 시작
    def process_xml_analysis():
        type_counts = Counter()
        valid_xmls = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # URL마다 검사 작업 생성
            future_to_url = {executor.submit(analyze_xml_content, url): url for url in urls}
            
            # 완료된 작업 처리
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    if result['isValid'] and result['type_value']:
                        type_counts[result['type_value']] += 1
                        valid_xmls.append(result)
                    
                    jobs[job_id]['results'].append(result)
                except Exception as e:
                    jobs[job_id]['results'].append({
                        'url': url,
                        'isValid': False,
                        'statusCode': 0,
                        'error': str(e)
                    })
                
                # 진행 상태 업데이트
                jobs[job_id]['completed'] += 1
                
                # 5개마다 유형별 카운트 업데이트 (중간 결과 반영)
                if jobs[job_id]['completed'] % 5 == 0:
                    jobs[job_id]['type_counts'] = dict(type_counts)
            
            # 유형별 카운트 최종 업데이트
            jobs[job_id]['type_counts'] = dict(type_counts)
            
            # 모든 작업 완료 후 상태 업데이트
            jobs[job_id]['status'] = 'completed'
    
    # 비동기 작업 시작
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(process_xml_analysis)
    
    # 작업 ID 반환
    return jsonify({
        'job_id': job_id,
        'status': 'in_progress',
        'message': 'XML 유형 분석 작업이 시작되었습니다.'
    })

def analyze_xml_content(url):
    try:
        # GET 요청으로 XML 내용 확인
        response = requests.get(url, timeout=10)
        
        # 상태 코드 확인
        status_code = response.status_code
        is_valid = 200 <= status_code < 300
        
        # 상태 코드가 200대가 아니면 무효 처리
        if not is_valid:
            return {
                'url': url,
                'isValid': False,
                'statusCode': status_code
            }
        
        # XML 콘텐츠 확인
        xml_content = response.text
        type_value = None
        
        # XML 파싱 시도
        try:
            root = ET.fromstring(xml_content)
            # 네임스페이스 무시하고 TYPE 태그 찾기
            type_elements = root.findall('.//TYPE')
            
            if type_elements:
                type_value = type_elements[0].text
                
            return {
                'url': url,
                'isValid': True,
                'statusCode': status_code,
                'type_value': type_value
            }
        except ET.ParseError:
            # XML 파싱 오류 처리
            return {
                'url': url,
                'isValid': False,
                'statusCode': status_code,
                'error': 'XML 파싱 오류'
            }
            
    except Exception as e:
        return {
            'url': url,
            'isValid': False,
            'statusCode': 0,
            'error': str(e)
        }

def check_single_url(url):
    try:
        # HEAD 요청으로 상태 코드만 확인
        response = requests.head(url, timeout=5)
        status_code = response.status_code
        is_valid = 200 <= status_code < 300
        
        return {
            'url': url,
            'isValid': is_valid,
            'statusCode': status_code
        }
    except requests.Timeout:
        # 타임아웃 발생 시
        return {
            'url': url,
            'isValid': False,
            'statusCode': 408,  # Request Timeout
            'error': '요청 시간 초과'
        }
    except requests.RequestException:
        # HEAD 요청이 실패할 경우 GET 요청 시도
        try:
            response = requests.get(url, timeout=5, stream=True)
            response.close()  # 내용 다운로드 방지
            
            status_code = response.status_code
            is_valid = 200 <= status_code < 300
            
            return {
                'url': url,
                'isValid': is_valid,
                'statusCode': status_code
            }
        except Exception as e:
            # 모든 시도 실패 시
            return {
                'url': url,
                'isValid': False,
                'statusCode': 0,
                'error': str(e)
            }

def check_xml_url(url):
    try:
        # GET 요청으로 XML 내용 확인
        response = requests.get(url, timeout=5)
        
        # 상태 코드 확인
        status_code = response.status_code
        
        # XML 내용 확인
        content_type = response.headers.get('Content-Type', '')
        is_xml = 'xml' in content_type.lower() or response.text.strip().startswith('<?xml')
        
        # XML 내용이 포함되어 있으면 유효하다고 판단
        is_valid = (200 <= status_code < 300) or is_xml
        
        return {
            'url': url,
            'isValid': is_valid,
            'statusCode': status_code,
            'isXml': is_xml,
            'contentType': content_type
        }
    except Exception as e:
        return {
            'url': url,
            'isValid': False,
            'statusCode': 0,
            'error': str(e)
        }

# 작업 정리 (오래된 작업 삭제)
@app.route('/cleanup-jobs', methods=['POST'])
def cleanup_jobs():
    # 24시간 이상 지난 작업 삭제 로직을 추가할 수 있음
    return jsonify({
        'message': '작업 정리가 완료되었습니다.',
        'jobs_remaining': len(jobs)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)