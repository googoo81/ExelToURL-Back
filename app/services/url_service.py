import requests
from config import Config

def check_single_url(url):
    """
    Check if a URL is valid by making a HEAD request, falling back to GET if needed.
    
    Args:
        url (str): The URL to check
        
    Returns:
        dict: Result with URL status information
    """
    try:
        # Try HEAD request first (faster, doesn't download content)
        response = requests.head(url, timeout=Config.REQUEST_TIMEOUT)
        status_code = response.status_code
        is_valid = 200 <= status_code < 300
        
        return {
            'url': url,
            'isValid': is_valid,
            'statusCode': status_code
        }
    except requests.Timeout:
        # Handle timeout
        return {
            'url': url,
            'isValid': False,
            'statusCode': 408,  # Request Timeout
            'error': '요청 시간 초과'
        }
    except requests.RequestException:
        # If HEAD fails, try GET with streaming (to avoid downloading full content)
        try:
            response = requests.get(url, timeout=Config.REQUEST_TIMEOUT, stream=True)
            response.close()  # Close connection to prevent downloading content
            
            status_code = response.status_code
            is_valid = 200 <= status_code < 300
            
            return {
                'url': url,
                'isValid': is_valid,
                'statusCode': status_code
            }
        except Exception as e:
            # All attempts failed
            return {
                'url': url,
                'isValid': False,
                'statusCode': 0,
                'error': str(e)
            }