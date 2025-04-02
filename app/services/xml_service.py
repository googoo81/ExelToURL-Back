import requests
import xml.etree.ElementTree as ET
from config import Config

def check_xml_url(url):
    """
    Check if a URL contains valid XML content.
    
    Args:
        url (str): The URL to check
        
    Returns:
        dict: Result with XML status information
    """
    try:
        # GET request to check XML content
        response = requests.get(url, timeout=Config.REQUEST_TIMEOUT)
        
        # Check status code
        status_code = response.status_code
        
        # Check if content appears to be XML
        content_type = response.headers.get('Content-Type', '')
        is_xml = 'xml' in content_type.lower() or response.text.strip().startswith('<?xml')
        
        # Consider valid if status code is good or content is XML
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

def analyze_xml_content(url):
    """
    Analyze XML content at the specified URL, looking for TYPE tags.
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        dict: Result with XML analysis information
    """
    try:
        # GET request to retrieve XML content
        response = requests.get(url, timeout=Config.XML_REQUEST_TIMEOUT)
        
        # Check status code
        status_code = response.status_code
        is_valid = 200 <= status_code < 300
        
        # If status code is not in 200s, return invalid result
        if not is_valid:
            return {
                'url': url,
                'isValid': False,
                'statusCode': status_code
            }
        
        # Get XML content and try to parse
        xml_content = response.text
        type_value = None
        
        try:
            # Parse XML and find TYPE tags
            root = ET.fromstring(xml_content)
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
            # XML parsing error
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