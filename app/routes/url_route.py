from flask import Blueprint, request, jsonify
import uuid
import concurrent.futures

from app.models.job import job_manager
from app.services.url_service import check_single_url

url_bp = Blueprint('url', __name__)

@url_bp.route('/')
def home():
    """Base route"""
    return "URL 유효성 검사 서비스가 실행 중입니다."

@url_bp.route('/check-url', methods=['GET'])
def check_url():
    """Check a single URL synchronously"""
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'error': 'URL이 제공되지 않았습니다.'
        }), 400
    
    # Use the service to check the URL
    result = check_single_url(url)
    return jsonify(result)

@url_bp.route('/start-validation', methods=['POST'])
def start_validation():
    """Start asynchronous validation of multiple URLs"""
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({
            'error': 'URLs가 제공되지 않았습니다.'
        }), 400
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    urls = data['urls']
    
    # Initialize job in the job manager
    job_manager.create_job(job_id, urls)
    
    # Start background processing
    def process_urls():
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(check_single_url, url): url for url in urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = {
                        'url': url,
                        'isValid': False,
                        'statusCode': 0,
                        'error': str(e)
                    }
                    
                job_manager.update_job_progress(job_id, result)
            
            # Mark job as complete
            job_manager.complete_job(job_id)
    
    # Start the background task
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(process_urls)
    
    # Return job ID to client
    return jsonify({
        'job_id': job_id,
        'status': 'in_progress',
        'message': '검증 작업이 시작되었습니다.'
    })

@url_bp.route('/job-status/<job_id>', methods=['GET'])
def job_status(job_id):
    """Check the status of a job"""
    job = job_manager.get_job(job_id)
    
    if not job:
        return jsonify({
            'error': '존재하지 않는 작업 ID입니다.'
        }), 404
    
    # If job is complete, return full results
    if job['status'] == 'completed':
        response_data = {
            'status': 'completed',
            'progress': 100,
            'results': job['results']
        }
        
        # Include type counts if available
        if 'type_counts' in job:
            response_data['type_counts'] = job['type_counts']
            
        return jsonify(response_data)
    
    # Calculate progress for in-progress jobs
    progress = int((job['completed'] / job['total']) * 100) if job['total'] > 0 else 0
    
    response_data = {
        'status': 'in_progress',
        'progress': progress,
        'completed': job['completed'],
        'total': job['total']
    }
    
    # Include partial type counts if available
    if 'type_counts' in job:
        response_data['type_counts'] = job['type_counts']
        
    return jsonify(response_data)

@url_bp.route('/cleanup-jobs', methods=['POST'])
def cleanup_jobs():
    """Remove old jobs to free up memory"""
    from config import Config
    
    removed_count = job_manager.cleanup_old_jobs(Config.JOB_CLEANUP_HOURS)
    
    return jsonify({
        'message': f'작업 정리가 완료되었습니다. {removed_count}개 작업이 삭제됨.',
        'jobs_remaining': len(job_manager.jobs)
    })