from flask import Blueprint, request, jsonify
import uuid
import concurrent.futures

from app.models.job import job_manager
from app.services.xml_service import check_xml_url, analyze_xml_content

xml_bp = Blueprint('xml', __name__)

@xml_bp.route('/start-xml-validation', methods=['POST'])
def start_xml_validation():
    """Start asynchronous validation of XML URLs"""
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
    def process_xml_urls():
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(check_xml_url, url): url for url in urls}
            
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
    executor.submit(process_xml_urls)
    
    # Return job ID to client
    return jsonify({
        'job_id': job_id,
        'status': 'in_progress',
        'message': 'XML 검증 작업이 시작되었습니다.'
    })

@xml_bp.route('/analyze-xml-types', methods=['POST'])
def analyze_xml_types():
    """Start asynchronous analysis of XML types"""
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({
            'error': 'URLs가 제공되지 않았습니다.'
        }), 400
    
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    urls = data['urls']
    
    # Initialize job in the job manager (with xml_analysis type)
    job_manager.create_job(job_id, urls, job_type="xml_analysis")
    
    # Start background processing
    def process_xml_analysis():
        valid_xmls = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(analyze_xml_content, url): url for url in urls}
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    
                    # Update type counts if valid XML with a type value
                    if result['isValid'] and 'type_value' in result and result['type_value']:
                        job_manager.update_type_counts(job_id, result['type_value'])
                        valid_xmls.append(result)
                        
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
    executor.submit(process_xml_analysis)
    
    # Return job ID to client
    return jsonify({
        'job_id': job_id,
        'status': 'in_progress',
        'message': 'XML 유형 분석 작업이 시작되었습니다.'
    })