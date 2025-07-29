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


class UnsplashObject:

    """
    A class that represents a custom object for the library.
    """

    def __init__(self, _data: dict):
        self._data = _data
        for key, value in _data.items():

            if key == "links":
                if "download" in value:
                    self.download_url = value["download"]
                if "html" in value:
                    self.html_url = value["html"]
            else:
                if isinstance(value, dict):
                    value = UnsplashObject(value)
                self.__setattr__(key, value)

    def __eq__(self, other):
        if not isinstance(other, UnsplashObject):
            return False
        return self._data == other._data
