import os

import requests
from filelock import FileLock
from tqdm import tqdm


def does_file_at_url_exist(url: str) -> bool:
    response = requests.get(url, stream=True)

    if response.status_code != 200:
        return False

    content_type = response.headers.get("content-type")

    return content_type is None or (not content_type.startswith("text/html"))


def download_with_progress_bar(
    url: str, save_path: str, desc: str = "", overwrite: bool = False
):
    if os.path.exists(save_path) and not overwrite:
        print(f"File already exists: {save_path}")
        return

    with open(save_path, "wb") as f:
        print(f"Downloading {save_path}")
        response = requests.get(url, stream=True)
        total_length = response.headers.get("content-length")

        content_type = response.headers.get("content-type")
        if content_type is not None and content_type.startswith("text/html"):
            raise ValueError(f"Invalid URL: {url}")

        if total_length is None:  # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            with tqdm(total=total_length, unit="B", unit_scale=True, desc=desc) as pbar:
                for data in response.iter_content(chunk_size=4096):
                    dl += len(data)
                    f.write(data)
                    pbar.update(len(data))


def download_with_locking(url: str, save_path: str, lock_path: str, desc: str = ""):
    with FileLock(lock_path):
        if not os.path.exists(save_path):
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            download_with_progress_bar(url=url, save_path=save_path, desc=desc)
