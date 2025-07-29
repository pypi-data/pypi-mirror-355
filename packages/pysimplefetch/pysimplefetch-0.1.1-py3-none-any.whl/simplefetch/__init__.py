import os

def download_file(url: str, output: str = ""):
    """
    Args:
        url (str): The URL to download.
        output (str): The output filename (optional).
    """
    command = f"wget {url}"
    if output:
        command += f" -O {output}"
    os.system(command)
