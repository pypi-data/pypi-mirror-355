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


from typing import Optional, List, Literal

from .models import UnsplashObject
from .utils import _get, _put, _post, _delete


class Client:

    """
    A client for interacting with the Unsplash API.

    :param access_key: Your Unsplash API access key.
    :type access_key: str
    :param secret_key: Your Unsplash API secret key.
    :type secret_key: Optional[str]
    """

    def __init__(self, access_key: str, secret_key: Optional[str] = None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.rate_limit = None
        self.rate_limit_remaining = None
        self.total_pages = None

    def get_current_user(self) -> UnsplashObject:
        """
        Get the current authenticated user.

        .. note::

            To access private user data, you must authenticate with the `read_user` scope.
        """
        return UnsplashObject(_get(self, "/me"))

    def update_current_user(
        self,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        url: Optional[str] = None,
        location: Optional[str] = None,
        bio: Optional[str] = None,
        instagram_username: Optional[str] = None,
    ) -> UnsplashObject:
        """
        Update the current user's profile information.

        .. note::

            This action requires the `write_user` scope.
        """
        data = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "url": url,
            "location": location,
            "bio": bio,
            "instagram_username": instagram_username
        }
        return UnsplashObject(_put(self, "/me", data=data))

    def get_user(self, username: str) -> UnsplashObject:
        """
        Get a user by their username.

        :param username: The username of the user to retrieve.
        :type username: str
        """
        return UnsplashObject(_get(self, f"/users/{username}"))

    def get_user_portfolio(self, username: str) -> str:
        """
        Get a user's portfolio URL by their username.

        :param username: The username of the user whose portfolio to retrieve.
        :type username: str
        """
        portfolio = _get(self, f"/users/{username}/portfolio")
        return portfolio["url"]

    def get_user_photos(
        self,
        username: str,
        *,
        page: Optional[int] = 1,
        per_page: Optional[int] = 10,
        order_by: Literal["latest", "oldest", "popular", "views", "downloads"] = "latest",
        stats: bool = False,
        resolution: Optional[str] = "days",
        quantity: Optional[int] = 30,
        orientation: Optional[Literal["landscape", "portrait", "squarish"]] = None
    ) -> List[UnsplashObject]:
        """
        Get a user's photos.

        :param username: The username of the user whose photos to retrieve.
        :type username: str
        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of photos to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        :param order_by: The order in which to retrieve the photos.
        :type order_by: Literal["latest", "oldest", "popular", "views", "downloads"]
        :param stats: Whether to include photo statistics.
        :type stats: bool
        :param resolution: The frequency of the statistics to retrieve.
        :type resolution: Optional[str]
        :param quantity: The number of statistics to retrieve.
        :type quantity: Optional[int]
        :param orientation: The orientation of the photos to retrieve.
        :type orientation: Optional[Literal["landscape", "portrait", "squarish"]]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "page": page,
            "per_page": per_page,
            "order_by": order_by,
            "stats": stats,
            "resolution": resolution,
            "quantity": quantity,
            "orientation": orientation
        }
        photos = _get(self, f"/users/{username}/photos", params=params)
        return [UnsplashObject(photo) for photo in photos]

    def get_user_likes(
        self,
        username: str,
        *,
        page: Optional[int] = 1,
        per_page: Optional[int] = 10,
        order_by: Literal["latest", "oldest", "popular"] = "latest",
        orientation: Optional[Literal["landscape", "portrait", "squarish"]] = None
    ) -> List[UnsplashObject]:
        """
        Get a user's liked photos.

        :param username: The username of the user whose liked photos to retrieve.
        :type username: str
        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of photos to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        :param order_by: The order in which to retrieve the photos.
        :type order_by: Literal["latest", "oldest", "popular", "views", "downloads"]
        :param orientation: The orientation of the photos to retrieve.
        :type orientation: Optional[Literal["landscape", "portrait", "squarish"]]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "page": page,
            "per_page": per_page,
            "order_by": order_by,
            "orientation": orientation
        }
        photos = _get(self, f"/users/{username}/likes", params=params)
        return [UnsplashObject(photo) for photo in photos]

    def get_user_collections(self, username: str, *, page: Optional[int] = 1, per_page: Optional[int] = 10) -> List[UnsplashObject]:
        """
        Get a user's collections.

        :param username: The username of the user whose collections to retrieve.
        :type username: str
        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of collections to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "page": page,
            "per_page": per_page
        }
        collections = _get(self, f"/users/{username}/collections", params=params)
        return [UnsplashObject(collection) for collection in collections]

    def get_user_statistics(
        self,
        username: str,
        *,
        resolution: Optional[str] = "days",
        quantity: Optional[int] = 30
    ) -> UnsplashObject:
        """
        Get a user's statistics.

        :param username: The username of the user whose statistics to retrieve.
        :type username: str
        :param resolution: The frequency of the statistics to retrieve.
        :type resolution: Optional[str]
        :param quantity: The number of statistics to retrieve.
        :type quantity: Optional[int]
        """
        params = {
            "resolution": resolution,
            "quantity": quantity
        }
        return UnsplashObject(_get(self, f"/users/{username}/statistics", params=params))

    def list_photos(self, *, page: Optional[int] = 1, per_page: Optional[int] = 10) -> List[UnsplashObject]:
        """
        List photos on a single page from the Editorial feed.

        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of photos to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "page": page,
            "per_page": per_page
        }
        photos = _get(self, "/photos", params=params)
        return [UnsplashObject(photo) for photo in photos]

    def get_photo(self, photo_id: str) -> UnsplashObject:
        """
        Get a photo by its ID.

        :param photo_id: The ID of the photo to retrieve.
        :type photo_id: str
        """
        return UnsplashObject(_get(self, f"/photos/{photo_id}"))

    def get_random_photo(
        self,
        *,
        collection_ids: Optional[List[str]] = None,
        topic_ids: Optional[List[str]] = None,
        username: Optional[str] = None,
        query: Optional[str] = None,
        orientation: Optional[Literal["landscape", "portrait", "squarish"]] = None,
        content_filter: Optional[Literal["low", "high"]] = "low",
        count: Optional[int] = 1
    ) -> List[UnsplashObject]:
        """
        Get a random photo or photos.

        :param collection_ids: A list of collection IDs to filter the random photo from.
        :type collection_ids: Optional[List[str]]
        :param topic_ids: A list of topic IDs to filter the random photo from.
        :type topic_ids: Optional[List[str]]
        :param username: The username of the user to filter the random photo from.
        :type username: Optional[str]
        :param query: A search query to filter the random photo.
        :type query: Optional[str]
        :param orientation: The orientation of the random photo.
        :type orientation: Optional[Literal["landscape", "portrait", "squarish"]]
        :param content_filter: The content filter level for the random photo.
        :type content_filter: Optional[Literal["low", "high"]]
        :param count: The number of random photos to retrieve. Must be between 1 and 30.
        :type count: Optional[int]
        """
        if count is not None and not 1 <= count <= 30:
            raise ValueError("'count' must be between 1 and 30")
        params = {
            "collections": ",".join(collection_ids) if collection_ids else None,
            "topics": ",".join(topic_ids) if topic_ids else None,
            "username": username,
            "query": query,
            "orientation": orientation,
            "content_filter": content_filter,
            "count": count
        }
        photos = _get(self, "/photos/random", params=params)
        return [UnsplashObject(photo) for photo in photos]

    def get_photo_statistics(
        self,
        photo_id: str,
        *,
        resolution: Optional[str] = "days",
        quantity: Optional[int] = 30
    ) -> UnsplashObject:
        """
        Get statistics for a photo.

        :param photo_id: The ID of the photo to retrieve statistics for.
        :type photo_id: str
        :param resolution: The frequency of the statistics to retrieve.
        :type resolution: Optional[str]
        :param quantity: The number of statistics to retrieve.
        :type quantity: Optional[int]
        """
        params = {
            "resolution": resolution,
            "quantity": quantity
        }
        return UnsplashObject(_get(self, f"/photos/{photo_id}/statistics", params=params))

    def trigger_photo_download(
        self,
        photo_id: str
    ) -> str:
        """
        Trigger a download for a photo.

        .. note::

            This is purely an event endpoint used to increment the number of downloads a photo has. This endpoint is not to be used to embed the photo, it is for tracking purposes only.

        :param photo_id: The ID of the photo to trigger the download for.
        :type photo_id: str
        """
        return _get(self, f"/photos/{photo_id}/download")

    def update_photo(
        self,
        photo_id: str,
        *,
        description: Optional[str] = None,
        show_on_profile: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        location: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
        exposure_time: Optional[str] = None,
        aperture: Optional[str] = None,
        focal_length: Optional[str] = None,
        iso: Optional[int] = None
    ) -> UnsplashObject:
        """
        Update a photo's metadata.

        .. note::

            This action requires the `write_photos` scope.

        :param photo_id: The ID of the photo to update.
        :type photo_id: str
        :param description: The new description for the photo.
        :type description: Optional[str]
        :param show_on_profile: Whether to show the photo on the user's profile.
        :type show_on_profile: Optional[bool]
        :param tags: A list of tags to associate with the photo.
        :type tags: Optional[List[str]]
        :param latitude: The latitude of the photo's location (rounded to 6 decimals).
        :type latitude: Optional[float]
        :param longitude: The longitude of the photo's location (rounded to 6 decimals).
        :type longitude: Optional[float]
        :param location: The name of the location of the photo (including city and country).
        :type location: Optional[str]
        :param city: The city where the photo was taken.
        :type city: Optional[str]
        :param country: The country where the photo was taken.
        :type country: Optional[str]
        :param make: The camera make used to take the photo.
        :type make: Optional[str]
        :param model: The camera model used to take the photo.
        :type model: Optional[str]
        :param exposure_time: The exposure time of the camera when the photo was taken.
        :type exposure_time: Optional[str]
        :param aperture: The aperture value of the camera when the photo was taken.
        :type aperture: Optional[str]
        :param focal_length: The focal length of the camera when the photo was taken.
        :type focal_length: Optional[str]
        :param iso: The ISO speed rating of the camera when the photo was taken.
        :type iso: Optional[int]
        """
        data = {
            "description": description,
            "show_on_profile": show_on_profile,
            "tags": tags,
            "location[latitude]": latitude,
            "location[longitude]": longitude,
            "location[name]": location,
            "location[city]": city,
            "location[country]": country,
            "exif[make]": make,
            "exif[model]": model,
            "exif[exposure_time]": exposure_time,
            "exif[aperture_value]": aperture,
            "exif[focal_length]": focal_length,
            "exif[iso_speed_ratings]": iso
        }
        return UnsplashObject(_put(self, f"/photos/{photo_id}", data=data))

    def like_photo(
        self,
        photo_id: str
    ) -> UnsplashObject:
        """
        Like a photo.

        .. note::

            This action requires the `write_likes` scope.

        :param photo_id: The ID of the photo to like.
        :type photo_id: str
        """
        return UnsplashObject(_post(self, f"/photos/{photo_id}/like"))

    def unlike_photo(
        self,
        photo_id: str
    ) -> UnsplashObject:
        """
        Unlike a photo.

        .. note::

            This action requires the `write_likes` scope.

        :param photo_id: The ID of the photo to unlike.
        :type photo_id: str
        """
        return UnsplashObject(_delete(self, f"/photos/{photo_id}/like"))

    def search_photos(
        self,
        query: str,
        *,
        page: Optional[int] = 1,
        per_page: Optional[int] = 10,
        order_by: Literal["latest", "relevant"] = "relevant",
        collection_ids: Optional[List[str]] = None,
        content_filter: Optional[Literal["low", "high"]] = "low",
        color: Optional[Literal["black_and_white", "black", "white", "yellow", "orange", "red", "purple", "magenta", "green", "teal", "blue"]] = None,
        orientation: Optional[Literal["landscape", "portrait", "squarish"]] = None,
        language: Optional[str] = "en"
    ) -> List[UnsplashObject]:
        """
        Search for photos.

        :param query: The search query.
        :type query: str
        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of photos to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        :param order_by: The order in which to retrieve the photos.
        :type order_by: Literal["latest", "relevant"]
        :param collection_ids: A list of collection IDs to filter the search results.
        :type collection_ids: Optional[List[str]]
        :param content_filter: The content filter level for the search results.
        :type content_filter: Optional[Literal["low", "high"]]
        :param color: The color filter for the search results.
        :type color: Optional[Literal["black_and_white", "black", "white", "yellow", "orange", "red", "purple", "magenta", "green", "teal", "blue"]]
        :param orientation: The orientation of the photos to retrieve.
        :type orientation: Optional[Literal["landscape", "portrait", "squarish"]]
        :param language: The ISO 639-1 language code for the search results (for access this beta parameter, email `api@unsplash.com <mailto:api@unsplash.com>`_ with your application ID)
        :type language: Optional[str]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "query": query,
            "page": page,
            "per_page": per_page,
            "order_by": order_by,
            "collections": ",".join(collection_ids) if collection_ids else None,
            "content_filter": content_filter,
            "color": color,
            "orientation": orientation,
            "language": language
        }
        photos = _get(self, "/search/photos", params=params)
        return [UnsplashObject(photo) for photo in photos["results"]]

    def search_collections(
        self,
        query: str,
        *,
        page: Optional[int] = 1,
        per_page: Optional[int] = 10
    ) -> List[UnsplashObject]:
        """
        Search for collections.

        :param query: The search query.
        :type query: str
        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of collections to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "query": query,
            "page": page,
            "per_page": per_page
        }
        collections = _get(self, "/search/collections", params=params)
        return [UnsplashObject(collection) for collection in collections["results"]]

    def search_users(
        self,
        query: str,
        *,
        page: Optional[int] = 1,
        per_page: Optional[int] = 10
    ) -> List[UnsplashObject]:
        """
        Search for users.

        :param query: The search query.
        :type query: str
        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of users to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "query": query,
            "page": page,
            "per_page": per_page
        }
        users = _get(self, "/search/users", params=params)
        return [UnsplashObject(user) for user in users["results"]]

    def list_collections(
        self,
        *,
        page: Optional[int] = 1,
        per_page: Optional[int] = 10
    ) -> List[UnsplashObject]:
        """
        Get a single page from the list of all collections.

        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of collections to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "page": page,
            "per_page": per_page
        }
        collections = _get(self, "/collections", params=params)
        return [UnsplashObject(collection) for collection in collections]

    def get_collection(self, collection_id: str) -> UnsplashObject:
        """
        Get a collection by its ID.

        :param collection_id: The ID of the collection to retrieve.
        :type collection_id: str
        """
        return UnsplashObject(_get(self, f"/collections/{collection_id}"))

    def get_collection_photos(self, collection_id: str, *, page: Optional[int] = 1, per_page: Optional[int] = 10, orientation: Optional[Literal["landscape", "portrait", "squarish"]] = None) -> List[UnsplashObject]:
        """
        Get photos from a collection.

        :param collection_id: The ID of the collection to retrieve photos from.
        :type collection_id: str
        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of photos to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        :param orientation: The orientation of the photos to retrieve.
        :type orientation: Optional[Literal["landscape", "portrait", "squarish"]]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "page": page,
            "per_page": per_page,
            "orientation": orientation
        }
        photos = _get(self, f"/collections/{collection_id}/photos", params=params)
        return [UnsplashObject(photo) for photo in photos]

    def get_related_collections(self, collection_id: str) -> List[UnsplashObject]:
        """
        Get collections related to a specific collection.

        :param collection_id: The ID of the collection to retrieve related collections for.
        :type collection_id: str
        """
        collections = _get(self, f"/collections/{collection_id}/related")
        return [UnsplashObject(collection) for collection in collections]

    def create_collection(self, title: str, description: Optional[str] = None, private: Optional[bool] = False) -> UnsplashObject:
        """
        Create a new collection.

        .. note::

            This action requires the `write_collections` scope.

        :param title: The title of the collection.
        :type title: str
        :param description: The description of the collection.
        :type description: Optional[str]
        :param private: Whether the collection is private.
        :type private: Optional[bool]
        """
        data = {
            "title": title,
            "description": description,
            "private": private
        }
        return UnsplashObject(_post(self, "/collections", data=data))

    def update_collection(self, collection_id: str, *, title: Optional[str] = None, description: Optional[str] = None, private: Optional[bool] = None) -> UnsplashObject:
        """
        Update a collection's metadata.

        .. note::

            This action requires the `write_collections` scope.

        :param collection_id: The ID of the collection to update.
        :type collection_id: str
        :param title: The new title for the collection.
        :type title: Optional[str]
        :param description: The new description for the collection.
        :type description: Optional[str]
        :param private: Whether the collection is private.
        :type private: Optional[bool]
        """
        data = {
            "title": title,
            "description": description,
            "private": private
        }
        return UnsplashObject(_put(self, f"/collections/{collection_id}", data=data))

    def delete_collection(self, collection_id: str) -> None:
        """
        Delete a collection.

        .. note::

            This action requires the `write_collections` scope.

        :param collection_id: The ID of the collection to delete.
        :type collection_id: str
        """
        _delete(self, f"/collections/{collection_id}")

    def add_photo_to_collection(self, collection_id: str, photo_id: str) -> UnsplashObject:
        """
        Add a photo to a collection.

        .. note::

            This action requires the `write_collections` scope.

        :param collection_id: The ID of the collection to add the photo to.
        :type collection_id: str
        :param photo_id: The ID of the photo to add to the collection.
        :type photo_id: str
        """
        data = {
            "photo_id": photo_id
        }
        return UnsplashObject(_post(self, f"/collections/{collection_id}/add", data=data))

    def remove_photo_from_collection(self, collection_id: str, photo_id: str) -> UnsplashObject:
        """
        Remove a photo from a collection.

        .. note::

            This action requires the `write_collections` scope.

        :param collection_id: The ID of the collection to remove the photo from.
        :type collection_id: str
        :param photo_id: The ID of the photo to remove from the collection.
        :type photo_id: str
        """
        params = {
            "photo_id": photo_id
        }
        return _delete(self, f"/collections/{collection_id}/remove", params=params)

    def list_topics(
        self,
        *,
        page: Optional[int] = 1,
        per_page: Optional[int] = 10,
        order_by: Literal["featured", "latest", "oldest", "position"] = "position"
    ) -> List[UnsplashObject]:
        """
        List topics on a single page.

        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of topics to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        :param order_by: The order in which to retrieve the topics.
        :type order_by: Literal["featured", "latest", "oldest", "position"]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "page": page,
            "per_page": per_page,
            "order_by": order_by
        }
        topics = _get(self, "/topics", params=params)
        return [UnsplashObject(topic) for topic in topics]

    def get_topic(self, topic_id_or_slug: str) -> UnsplashObject:
        """
        Get a topic by its ID or slug.

        :param topic_id_or_slug: The ID or slug of the topic to retrieve.
        :type topic_id_or_slug: str
        """
        return UnsplashObject(_get(self, f"/topics/{topic_id_or_slug}"))

    def get_topic_photos(
        self,
        topic_id_or_slug: str,
        *,
        page: Optional[int] = 1,
        per_page: Optional[int] = 10,
        order_by: Literal["latest", "oldest", "popular"] = "latest",
        orientation: Optional[Literal["landscape", "portrait", "squarish"]] = None
    ) -> List[UnsplashObject]:
        """
        Get photos from a topic.

        :param topic_id_or_slug: The ID or slug of the topic to retrieve photos from.
        :type topic_id_or_slug: str
        :param page: The page number to retrieve.
        :type page: Optional[int]
        :param per_page: The number of photos to retrieve per page. Must be between 1 and 30.
        :type per_page: Optional[int]
        :param order_by: The order in which to retrieve the photos.
        :type order_by: Literal["latest", "oldest", "popular"]
        :param orientation: The orientation of the photos to retrieve.
        :type orientation: Optional[Literal["landscape", "portrait", "squarish"]]
        """
        if per_page is not None and not 1 <= per_page <= 30:
            raise ValueError("'per_page' must be between 1 and 30")
        params = {
            "page": page,
            "per_page": per_page,
            "order_by": order_by,
            "orientation": orientation
        }
        photos = _get(self, f"/topics/{topic_id_or_slug}/photos", params=params)
        return [UnsplashObject(photo) for photo in photos]

    def get_total_stats(self) -> UnsplashObject:
        """
        Get the total statistics for the Unsplash API.
        """
        return UnsplashObject(_get(self, "/stats/total"))

    def get_monthly_stats(self) -> UnsplashObject:
        """
        Get the overall statistics for the Unsplash API for the past 30 days.
        """
        return UnsplashObject(_get(self, "/stats/monthly"))
