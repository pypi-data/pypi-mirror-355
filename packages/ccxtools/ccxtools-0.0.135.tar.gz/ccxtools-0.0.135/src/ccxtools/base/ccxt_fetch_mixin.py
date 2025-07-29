from requests.exceptions import HTTPError


class CcxtFetchMixin:
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def fetch(self, url, method='GET', headers=None, body=None):        
        try:
            return super().fetch(url, method, headers, body)
        except Exception as original_error:
            # request 정보 수집
            request_info = {
                'method': method,
                'url': url,
                'headers': dict(headers or {}),
                'body': body
            }
            
            # response 정보 수집
            response_info = {}
            
            if hasattr(self, 'last_json_response'):
                response_info['body'] = self.last_json_response
            if hasattr(self, 'last_response_headers'):
                response_info['headers'] = dict(self.last_response_headers or {})
            if hasattr(original_error, '__cause__') and isinstance(original_error.__cause__, HTTPError):
                http_response = original_error.__cause__.response
                if http_response:
                    response_info['status_code'] = http_response.status_code
                    response_info['status_text'] = http_response.reason
            
            raise FetchError(request_info, response_info) from original_error
        

class FetchError(Exception):

    def __init__(self, request_info, response_info):
        self.request_info = request_info
        self.response_info = response_info
