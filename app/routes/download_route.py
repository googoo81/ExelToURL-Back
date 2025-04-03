from flask import Blueprint, request, jsonify, Response
import requests
import io
import zipfile
from app.services.download_service import download_single_xml, create_zip_from_urls, get_filename_from_url

# 블루프린트 생성
download_bp = Blueprint('download', __name__)

@download_bp.route('/download-xml', methods=['GET'])
def download_xml():
    """단일 XML 파일을 다운로드합니다."""
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'URL parameter is required'}), 400
    
    success, content, error = download_single_xml(url)
    
    if not success:
        return jsonify({'error': error}), 400
    
    # 파일명 생성
    filename = get_filename_from_url(url)
    
    # XML 파일을 클라이언트에게 전송
    return Response(
        content,
        mimetype='application/xml',
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )

@download_bp.route('/create-zip', methods=['POST'])
def create_zip():
    """여러 XML 파일을 다운로드하여 ZIP 파일로 압축합니다."""
    data = request.json
    urls = data.get('urls', [])
    
    if not urls:
        return jsonify({'error': 'No URLs provided'}), 400
    
    # 워커 수 설정 (선택적)
    worker_count = data.get('workerCount', 5)
    # Zip 파일명 설정 (선택적)
    zip_filename = data.get('filename', 'xml_files.zip')
    
    # ZIP 파일 생성
    success, memory_file, message = create_zip_from_urls(urls, worker_count)
    
    if not success:
        return jsonify({'error': message}), 400
    
    # ZIP 파일 반환
    return Response(
        memory_file.getvalue(),
        mimetype='application/zip',
        headers={'Content-Disposition': f'attachment; filename={zip_filename}'}
    )

@download_bp.route('/download-status', methods=['GET'])
def download_status():
    """다운로드 서비스 상태를 확인합니다."""
    return jsonify({
        'status': 'active',
        'message': 'XML 다운로드 서비스가 정상 작동 중입니다.'
    })