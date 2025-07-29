.. image:: https://raw.githubusercontent.com/Ombucha/unsplash.py/main/banner.png

.. image:: https://img.shields.io/pypi/v/unsplash-client
    :target: https://pypi.python.org/pypi/unsplash-client
    :alt: PyPI version
.. image:: https://img.shields.io/pypi/dm/unsplash-client
    :target: https://pypi.python.org/pypi/unsplash-client
    :alt: PyPI downloads
.. image:: https://sloc.xyz/github/Ombucha/unsplash.py
    :target: https://github.com/Ombucha/unsplash.py/graphs/contributors
    :alt: Lines of code
.. image:: https://img.shields.io/github/repo-size/Ombucha/unsplash.py
    :target: https://github.com/Ombucha/unsplash.py
    :alt: Repository size

A modern, Pythonic client for the Unsplash API.

Features
--------

* Search for photos, users, and collections
* Download and trigger downloads for Unsplash images
* Get random photos or curated collections
* Access user profiles and statistics
* Manage and create collections
* List and explore Unsplash topics
* Fully typed and Pythonic interface
* Handles Unsplash API rate limits and errors gracefully

Requirements
------------

* Python 3.8 or higher
* `requests <https://pypi.python.org/pypi/requests>`_ library

Installation
------------

Install the latest stable release from PyPI:

.. code-block:: sh

    # For Unix / macOS
    python3 -m pip install "unsplash.py"

    # For Windows
    py -m pip install "unsplash.py"

To install the latest development version:

.. code-block:: sh

    git clone https://github.com/Ombucha/unsplash.py
    cd unsplash.py
    pip install -e .

Quick Start
-----------

Here's how to use unsplash.py:

.. code-block:: python

    import unsplash

    # Initialize the client with your Unsplash API access key
    client = unsplash.Client(access_key="YOUR_ACCESS_KEY")

    # Search for photos
    photos = client.search_photos("mountains")
    for photo in photos:
        print(photo.urls["regular"])

    # Get a random photo
    random_photo = client.get_random_photo()
    print(random_photo[0].urls["full"])

    # Get user profile
    user = client.get_user("unsplash")
    print(user.name, user.bio)

Links
-----

- `Unsplash <https://unsplash.com/>`_
- `Official API <https://unsplash.com/developers>`_
- `Documentation <https://unsplash.readthedocs.io/>`_

Contributing
------------

Contributions are welcome! Please open an issue or pull request on GitHub.
For major changes, please open an issue first to discuss what you would like to change.
