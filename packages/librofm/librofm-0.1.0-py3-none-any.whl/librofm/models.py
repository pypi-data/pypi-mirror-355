from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class Credentials(BaseModel):
    """
    Represents the credentials required to access the LibroFM API.
    """
    access_token: str
    token_type: str
    created_at: int

class Audiobook(BaseModel):
    """
    Represents an audiobook with its metadata.
    """
    title: str
    isbn: int
    authors: list[str]
    cover_url: str
    catalog_info: dict
    audiobook_info: dict
    id: int
    subtitle: str | None
    publisher: str
    publication_date: datetime
    created_at: datetime
    updated_at: datetime
    description: str
    genres: list[dict]
    lead: str | None
    abridged: bool
    series: str | None
    series_num: int | None
    recommendations: list[dict]
    user_metadata: dict | None


class Page(BaseModel):
    """
    Represents pagination information for API responses.
    """
    page: int
    total_pages: int
    audiobooks: list[Audiobook]


class ManifestPart(BaseModel):
    """
    Represents a part of an audiobook, including its URL and size in bytes.
    """
    url: str
    size_bytes: int


class ManifestTrack(BaseModel):
    """
    Represents a track of an audiobook, including its number, length, chapter title, and timestamps.
    """
    number: int
    length_sec: int
    chapter_title: str | None
    created_at: datetime
    updated_at: datetime


class Manifest(BaseModel):
    """
    Represents metadata for an audiobook, including its parts and tracks.
    """
    isbn: int
    parts: list[ManifestPart]
    tracks: list[ManifestTrack]
    expires_at: datetime
    version: int
    size_bytes: int


class PackagedM4b(BaseModel):
    """
    Represents a packaged M4B file, including its URL and size in bytes.
    """
    m4b_url: str


class LibroFMClientSettings(BaseSettings):
    """
    Settings for the LibroFM client, including API credentials and endpoints.
    """
    username: str
    password: str

    class Config:
        env_file = ".env"
        env_prefix = "LIBROFM_"
