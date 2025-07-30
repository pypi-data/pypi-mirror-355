import requests
import os
import validators


def get_url_file_type(url):
    try:
        response = requests.head(url, allow_redirects=True)
        content_type = response.headers.get("content-type")
        return content_type
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def dir_path(string):
    if os.path.isdir(string) or validators.url(string):
        return string
    else:
        raise NotADirectoryError(string)


def file_path(string):
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)
