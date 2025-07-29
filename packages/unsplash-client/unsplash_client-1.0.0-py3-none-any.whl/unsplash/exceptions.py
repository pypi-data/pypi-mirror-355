"""
MIT License

Copyright (c) 2025 Omkaar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


class UnsplashException(Exception):
    """Base exception for Unsplash API errors."""
    def __init__(self, message="An error occurred with the Unsplash API."):
        super().__init__(message)
        self.message = message

class UnauthorizedException(UnsplashException):
    """Exception raised for unauthorized access."""
    def __init__(self, message="Unauthorized access. Please check your API key."):
        super().__init__(message)

class NotFoundException(UnsplashException):
    """Exception raised when a resource is not found."""
    def __init__(self, message="Resource not found. Please check the endpoint or parameters."):
        super().__init__(message)

class BadRequestException(UnsplashException):
    """Exception raised for bad requests."""
    def __init__(self, message="Bad request. Please check your request parameters."):
        super().__init__(message)

class ForbiddenException(UnsplashException):
    """Exception raised for forbidden access."""
    def __init__(self, message="Forbidden access. You do not have permission to access this resource."):
        super().__init__(message)

class InternalServerErrorException(UnsplashException):
    """Exception raised for internal server errors."""
    def __init__(self, message="Internal server error. Please try again later."):
        super().__init__(message)
