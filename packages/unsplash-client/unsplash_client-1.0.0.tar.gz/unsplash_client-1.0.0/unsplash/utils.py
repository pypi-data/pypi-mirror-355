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


from re import findall
from typing import Optional, Callable, TYPE_CHECKING
from urllib.parse import urlparse, parse_qs
from requests import get, put, post, delete

from .models import UnsplashObject
from .endpoints import BASE_URL, VERSION
from .exceptions import (
    UnauthorizedException,
    NotFoundException,
    BadRequestException,
    ForbiddenException,
    InternalServerErrorException
)

if TYPE_CHECKING:
    from .client import Client


def modify_image_url(
    url: str,
    *,
    width: Optional[float] = None,
    height: Optional[float] = None,
    file_format: Optional[str] = None,
    auto_format: Optional[bool] = None,
    quality: Optional[float] = None,
    fit: Optional[str] = None,
    crop: Optional[str] = None,
    pixel_ratio: Optional[float] = None
) -> str:
    """
    Modify an Unsplash image URL with various parameters.

    :param url: The original Unsplash image URL.
    :type url: str
    :param width: Desired width of the image.
    :type width: Optional[float]
    :param height: Desired height of the image.
    :type height: Optional[float]
    :param file_format: Desired image format.
    :type file_format: Optional[str]
    :param auto_format: Whether to automatically select format.
    :type auto_format: Optional[bool]
    :param quality: Desired image quality.
    :type quality: Optional[float]
    :param fit: Fit mode for the image.
    :type fit: Optional[str]
    :param crop: Crop mode for the image.
    :type crop: Optional[str]
    :param pixel_ratio: Pixel ratio for the image.
    :type pixel_ratio: Optional[float]
    """
    params = []
    if width is not None:
        params.append(f"w={int(width)}")
    if height is not None:
        params.append(f"h={int(height)}")
    if file_format is not None:
        params.append(f"fm={file_format}")
    if auto_format:
        params.append("auto=format")
    if quality is not None:
        params.append(f"q={int(quality * 100)}")
    if fit is not None:
        params.append(f"fit={fit}")
    if crop is not None:
        params.append(f"crop={crop}")
    if pixel_ratio is not None:
        params.append(f"dpr={pixel_ratio}")

    if url.endswith("/"):
        url = url[:-1]

    if "?" in url:
        url += "&" + "&".join(params)
    else:
        url += "?" + "&".join(params)
    return url

def get_all_pages(client: "Client", function: Callable, *args, **kwargs):
    """
    Fetch all pages of results from a paginated API endpoint.

    . note::

        This function assumes that the API endpoint supports pagination.

    .. warn::

        This function will try to minimise the number of requests made to the API by setting `per_page` to 30, which is the maximum, but it can still make many requests.

    :param client: The Unsplash client instance.
    :type client: unsplash.Client
    :param function: The function to call for fetching each page.
    :type function: Callable
    :param args: Positional arguments for the function.
    :param kwargs: Keyword arguments for the function.
    :return: A list of all results from all pages.
    """
    results = []
    page = 1
    kwargs['page'] = page
    kwargs['per_page'] = 30
    response = function(*args, **kwargs)
    results.extend(response)

    for page in range(2, client.total_pages + 1):
        kwargs['page'] = page
        response = function(*args, **kwargs)
        results.extend(response)

    return results

def download_image(client: "Client", photo: UnsplashObject, file_path: str, *, width: Optional[float] = None, height: Optional[float] = None, file_format: Optional[str] = None, auto_format: Optional[bool] = None, quality: Optional[float] = None, fit: Optional[str] = None, crop: Optional[str] = None, pixel_ratio: Optional[float] = None) -> str:
    """
    Download an image from Unsplash with specified parameters.

    :param photo: The UnsplashObject representing the photo to download.
    :type photo: UnsplashObject
    :param width: Desired width of the image.
    :type width: Optional[float]
    :param height: Desired height of the image.
    :type height: Optional[float]
    :param file_format: Desired image format.
    :type file_format: Optional[str]
    :param auto_format: Whether to automatically select format.
    :type auto_format: Optional[bool]
    :param quality: Desired image quality.
    :type quality: Optional[float]
    :param fit: Fit mode for the image.
    :type fit: Optional[str]
    :param crop: Crop mode for the image.
    :type crop: Optional[str]
    :param pixel_ratio: Pixel ratio for the image.
    :type pixel_ratio: Optional[float]
    """
    if not isinstance(photo, UnsplashObject):
        raise TypeError("photo must be an instance of UnsplashObject")
    if not hasattr(photo, 'blur_hash'):
        raise TypeError("given UnsplashObject does not represent a photo")

    url = modify_image_url(photo.urls.raw, width=width, height=height, file_format=file_format, auto_format=auto_format, quality=quality, fit=fit, crop=crop, pixel_ratio=pixel_ratio)
    response = get(url, stream=True)

    with open(file_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    client.trigger_photo_download(photo.id)

def _raise_for_status(response):
    if response.status_code == 401:
        raise UnauthorizedException()
    if response.status_code == 404:
        raise NotFoundException()
    if response.status_code == 400:
        raise BadRequestException()
    if response.status_code == 403:
        raise ForbiddenException()
    if response.status_code in {500, 503}:
        raise InternalServerErrorException()
    return response

def _get(client, endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Accept-Version": VERSION,
        "Authorization": f"Client-ID {client.access_key}"
    }
    response = _raise_for_status(get(url, headers=headers, params=params))
    client.rate_limit = response.headers.get('X-RateLimit-Limit')
    client.rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')

    link_header = response.headers.get('Link')
    if link_header:
        matches = findall(r'<([^>]+)>;\s*rel="([^"]+)"', link_header)
        links = {rel: url for url, rel in matches}
        last_url = links.get("last")
        last_page = int(parse_qs(urlparse(last_url).query)['page'][0]) if last_url else None
        if last_page:
            client.total_pages = last_page

    return response.json()

def _put(client, endpoint, data=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Accept-Version": VERSION,
        "Authorization": f"Client-ID {client.access_key}"
    }
    response = _raise_for_status(put(url, headers=headers, json=data))
    client.rate_limit = response.headers.get('X-RateLimit-Limit')
    client.rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
    return response.json()

def _post(client, endpoint, data=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Accept-Version": VERSION,
        "Authorization": f"Client-ID {client.access_key}"
    }
    response = _raise_for_status(post(url, headers=headers, json=data))
    client.rate_limit = response.headers.get('X-RateLimit-Limit')
    client.rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
    return response.json()

def _delete(client, endpoint, params=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Accept-Version": VERSION,
        "Authorization": f"Client-ID {client.access_key}"
    }
    response = _raise_for_status(delete(url, headers=headers, params=params))
    client.rate_limit = response.headers.get('X-RateLimit-Limit')
    client.rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
    return response.json()
