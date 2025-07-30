class QuakeAPIException(Exception):
    """Base exception class for Quake API errors."""
    def __init__(self, message, api_code=None, response_status_code=None):
        super().__init__(message)
        self.api_code = api_code
        self.response_status_code = response_status_code
        self.message = message

    def __str__(self):
        return f"QuakeAPIException: {self.message} (API Code: {self.api_code}, HTTP Status: {self.response_status_code})"

class QuakeAuthException(QuakeAPIException):
    """Exception for authentication errors (e.g., invalid API key)."""
    def __str__(self):
        return f"QuakeAuthException: {self.message} (API Code: {self.api_code}, HTTP Status: {self.response_status_code})"

class QuakeRateLimitException(QuakeAPIException):
    """Exception for rate limiting errors."""
    def __str__(self):
        return f"QuakeRateLimitException: {self.message} (API Code: {self.api_code}, HTTP Status: {self.response_status_code})"

class QuakeInvalidRequestException(QuakeAPIException):
    """Exception for invalid request errors (e.g., bad parameters, query syntax error)."""
    def __str__(self):
        return f"QuakeInvalidRequestException: {self.message} (API Code: {self.api_code}, HTTP Status: {self.response_status_code})"

class QuakeServerException(QuakeAPIException):
    """Exception for server-side errors on Quake's end."""
    def __str__(self):
        return f"QuakeServerException: {self.message} (API Code: {self.api_code}, HTTP Status: {self.response_status_code})"
