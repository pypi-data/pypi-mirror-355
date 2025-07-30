import argparse
from pathlib import Path
import sys
from librofm.client import LibroFMClient
from librofm.util import clean_filename


def main():
    parser = argparse.ArgumentParser(description="Download audiobooks from Libro.fm")
    parser.add_argument(
        "base_path",
        nargs="?",
        default="~/Audiobooks",
        help="Base path for audiobook downloads (default: ~/Audiobooks)"
    )
    
    args = parser.parse_args()
    
    c = LibroFMClient.get_client()
    BASE_PATH = Path(args.base_path).expanduser()
    
    page = c.get_library(page=1)
    for idx, audiobook in enumerate(page.audiobooks):
        authors = Path(clean_filename(', '.join(audiobook.authors)))
        title = Path(clean_filename(audiobook.title))
        path = BASE_PATH / authors / title
        path.mkdir(parents=True, exist_ok=True)
        sys.stdout.write(f"\r⏳ Downloading {audiobook.title} {idx}")
        sys.stdout.flush()
        try:
            success = c.download(audiobook, path)
            if not success:
                print(f"\rFailed to download {audiobook.title}")
        except Exception as e:
            print(f"\rError downloading {audiobook.title}: {e}")
        print(f"\r✓ Downloaded {audiobook.title} {idx}   ")


if __name__ == "__main__":
    main()
