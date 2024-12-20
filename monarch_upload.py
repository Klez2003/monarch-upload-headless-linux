import os
import sys
import json
import requests

CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB
UPLOAD_URL = "https://api.monarchupload.cc/v3/upload"
CONFIG_FILE = "monarch_config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        default_config = {
            "upload_secret": ""
        }
        with open(CONFIG_FILE, "w") as config_file:
            json.dump(default_config, config_file, indent=4)
        print(f"[INFO] Configuration file created: {CONFIG_FILE}")
        print("[INFO] Please update the configuration file with your upload secret.")
        exit(1)

    with open(CONFIG_FILE, "r") as config_file:
        config = json.load(config_file)

    if not config.get("upload_secret"):
        print("[ERROR] Missing upload secret in monarch_config.json.")
        exit(1)

    return config


def is_file_in_use(file_path):
    try:
        with open(file_path, 'r+'):
            return False
    except (OSError, IOError):
        return True


def upload_file(file_path, upload_secret):
    if not os.path.exists(file_path):
        print(f"[ERROR] File does not exist: {file_path}")
        return

    print(f"[INFO] Uploading file: {file_path}")

    with open(file_path, "rb") as file_handle:
        last_chunk = False
        chunk = 0

        while True:
            file_handle.seek(chunk * CHUNK_SIZE)
            data = file_handle.read(CHUNK_SIZE)

            if len(data) < CHUNK_SIZE:
                last_chunk = True

            files = {
                "file": (os.path.basename(file_path), data),
                "secret": (None, upload_secret),
                "chunked": (None, "true"),
                "private": (None, "false"),
                "lastchunk": (None, "true" if last_chunk else "false"),
            }

            response = requests.post(UPLOAD_URL, files=files)
            if response.status_code != 200:
                print(f"[ERROR] Failed to upload. HTTP {response.status_code}")
                return

            response_data = response.json()

            if response_data.get("status") != "success" or last_chunk:
                print(f"[INFO] {response_data.get('message', 'Upload finished.')}")
                if response_data.get("data", {}).get("url"):
                    print(f"[INFO] Uploaded file URL: {response_data['data']['url']}")
                break

            chunk += 1


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 monarch_upload.py <file_path>")
        exit(1)

    file_path = sys.argv[1]
    config = load_config()
    upload_secret = config["upload_secret"]

    while is_file_in_use(file_path):
        print("[INFO] Waiting for the file to become available...")
        time.sleep(0.1)

    upload_file(file_path, upload_secret)


if __name__ == "__main__":
    main()
