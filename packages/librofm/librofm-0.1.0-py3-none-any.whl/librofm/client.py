
import os
from urllib import parse
import requests

from librofm.models import Audiobook, Credentials, LibroFMClientSettings, Manifest, PackagedM4b, Page
from librofm.util import get_isbn, requires_auth


BASE_URL = "https://libro.fm"
LOGIN_ENDPOINT = "/oauth/token"
LIBRARY_ENDPOINT = "/api/v7/library"
DOWNLOAD_ENDPOINT = "/api/v9/download-manifest"
PACKAGED_M4B_ENDPOINT = "/api/v10/audiobooks/{isbn}/packaged_m4b"

class LibroFMClient:
    @staticmethod
    def get_client():
        settings = LibroFMClientSettings()
        return LibroFMClient(settings.username, settings.password)
    
    def __init__(self, username:str, password:str) -> None:
        """
        Initializes the LibroFM client with the provided username and password.
        
        Args:
            username (str): The username for the LibroFM account.
            password (str): The password for the LibroFM account.
        """
        self.username = username
        self.password = password
        self.access_token = None

    def authenticate(self) -> None:
        """
        Authenticates the user with the LibroFM API and retrieves an access token.
        
        Raises:
            Exception: If authentication fails.
        """
        params = {
            "grant_type": "password",
            "username": self.username,
            "password": self.password,
        }
        response = self._do_post(LOGIN_ENDPOINT, params)
        token_data = Credentials(**response)

        if not token_data.access_token:
            raise Exception("Authentication failed. Please check your credentials.")
        
        self.access_token = token_data.access_token

    @requires_auth
    def get_library(self, page: int = 1) -> Page:
        """
        Retrieves the user's audiobook library from the LibroFM API.
        
        Args:
            page (int): The page number to retrieve (default is 1).
        
        Returns:
            dict: The response containing the user's audiobook library.
        """
        params = {"page": page}
        data = self._do_get(LIBRARY_ENDPOINT, params=params)
        return Page(**data)
    
    @requires_auth
    def get_download_manifest(self, audiobook: Audiobook | str) -> Manifest:
        """
        Retrieves the download manifest for a specific audiobook.
        
        Args:
            audiobook (Audiobook): The audiobook for which to retrieve the download manifest.
        
        Returns:
            dict: The response containing the download manifest.
        """
        isbn = get_isbn(audiobook)
        params = {"isbn": isbn}
        data = self._do_get(DOWNLOAD_ENDPOINT, params=params)
        return Manifest(**data)
    
    @requires_auth
    def get_packaged_m4b_info(self, audiobook: Audiobook | str) -> PackagedM4b | None:
        """
        Retrieves information about the packaged M4B for a specific audiobook.
        Args:
            audiobook (Audiobook): The audiobook for which to retrieve the packaged M4B information.
        Returns:
            PackagedM4b: The packaged M4B information for the audiobook.
        """
        isbn = get_isbn(audiobook)
        endpoint = PACKAGED_M4B_ENDPOINT.format(isbn=isbn)
        data = self._do_get(endpoint)
        if not data or "m4b_url" not in data:
            return None
        return PackagedM4b(**data)
    
    @requires_auth
    def download(self, audiobook: Audiobook | str, output_dir: str = ".") -> bool:
        """
        Downloads the audiobook in either MP3 or M4B format based on availability.
        
        Args:
            audiobook (Audiobook): The audiobook to download.
            output_dir (str): The directory where the audiobook will be saved.
        
        Returns:
            bool: True if the download was successful, False otherwise.
        """
        success = self.download_m4b(audiobook, output_dir)
        if success:
            return True
        
        return self.download_mp3(audiobook, output_dir)
    
    def download_mp3(self, audiobook: Audiobook | str, output_dir: str = ".") -> bool:
        """
        Downloads the audiobook by retrieving its download manifest.
        
        Args:
            audiobook (Audiobook): The audiobook to download.
        
        Returns:
            Manifest: The download manifest for the audiobook.
        """
        manifest = self.get_download_manifest(audiobook)
        if not manifest:
            return False
        
        for part in manifest.parts:
            part_url = part.url
            response = requests.get(part_url, stream=True)
            if response.status_code == 200:
                parsed = parse.urlparse(part_url)
                filename = parse.unquote(parsed.path.split('/')[-1])
                outpath = f"{output_dir}/{filename}"
                if os.path.exists(outpath):
                    return True
                with open(outpath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                print(f"Failed to download part: {part_url}")
                return False
        return True
            
    def download_m4b(self, audiobook: Audiobook | str, output_dir: str = ".") -> bool:
        """
        Downloads the audiobook in M4B format by retrieving its packaged info.
        
        Args:
            audiobook (Audiobook): The audiobook to download.
        
        Returns:
            PackagedM4B: The download manifest for the audiobook.
        """
        packaged = self.get_packaged_m4b_info(audiobook)
        if not packaged or not packaged.m4b_url:
            return False
        
        response = requests.get(packaged.m4b_url, stream=True)
        if response.status_code == 200:
            parsed = parse.urlparse(packaged.m4b_url)
            filename = parse.unquote(parsed.path.split('/')[-1])
            outpath = f"{output_dir}/{filename}"
            if os.path.exists(outpath):
                return True
            with open(outpath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        else:
            print(f"Failed to download part: {packaged.m4b_url}")
            return False
        return True
    
    def _do_post(self, endpoint: str, data: dict) -> dict:
        """
        Makes a POST request to the specified endpoint with the provided data.
        
        Args:
            endpoint (str): The API endpoint to send the request to.
            data (dict): The data to include in the POST request.
        
        Returns:
            dict: The response from the API.
        """
        return requests.post(f"{BASE_URL}{endpoint}", headers=self.headers, json=data).json()
    
    def _do_get(self, endpoint: str, params: dict = None) -> dict:
        """
        Makes a GET request to the specified endpoint with the provided parameters.
        
        Args:
            endpoint (str): The API endpoint to send the request to.
            params (dict, optional): The parameters to include in the GET request.
        
        Returns:
            dict: The response from the API.
        """
        return requests.get(f"{BASE_URL}{endpoint}", headers=self.headers, params=params).json()
    
    @property
    def headers(self) -> dict[str, str]:
        """
        Returns the headers required for API requests, including the access token.
        
        Returns:
            dict[str, str]: The headers for the API request.
        """
        h = {
            "Content-Type": "application/json",
        }
        if self.access_token:
            h["Authorization"] = f"Bearer {self.access_token}"
        return h
        