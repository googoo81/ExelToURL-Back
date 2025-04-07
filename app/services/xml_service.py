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
    Analyze XML content at the specified URL, looking for all required tags:
    COURSE_CODE, GRADE, SESSION, UNIT, PERIOD, ORDER, STUDY, TYPE, STYLE
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        dict: Result with XML analysis information including all tag contents
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
        
        # Default values for all tags
        tag_values = {
            'course_code': None,
            'grade': None,
            'session': None,
            'unit': None,
            'period': None,
            'order': None,
            'study': None,
            'type_value': None,
            'style_content': 'undefined'  # Default to undefined if tag doesn't exist
        }
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Tag mapping (XML tag name to our dictionary key)
            tag_mapping = {
                'COURSE_CODE': 'course_code',
                'GRADE': 'grade',
                'SESSION': 'session',
                'UNIT': 'unit',
                'PERIOD': 'period',
                'ORDER': 'order',
                'STUDY': 'study',
                'TYPE': 'type_value',
                'STYLE': 'style_content'
            }
            
            # Extract all requested tags
            for xml_tag, dict_key in tag_mapping.items():
                elements = root.findall(f'.//{xml_tag}')
                if elements and elements[0].text is not None:
                    # For STYLE tag, handle empty strings specially
                    if xml_tag == 'STYLE' and elements[0].text.strip() == "":
                        tag_values[dict_key] = "null"
                    else:
                        tag_values[dict_key] = elements[0].text.strip()
                elif xml_tag == 'STYLE' and (not elements or elements[0].text is None):
                    # Special handling for empty STYLE tag
                    if not elements:
                        tag_values[dict_key] = "undefined"
                    else:
                        tag_values[dict_key] = "null"
            
            # Create the result dictionary
            result = {
                'url': url,
                'isValid': True,
                'statusCode': status_code,
                **tag_values  # Include all tag values
            }
            
            return result
            
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