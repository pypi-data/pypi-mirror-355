import tempfile
from typing import Literal
from typing import Annotated, Union
from pydantic import BaseModel, Field, computed_field
import enum
import json


class AccessType(enum.Enum):
    READ = "read"
    WRITE = "write"


class StorageConfiguration(BaseModel, extra='allow'):
    type: str = Field(title='Type of storage used')
    is_local: bool


class FileStorageConfiguration(StorageConfiguration):
    type: Literal["file"] = "file"
    is_local: Literal[True] = True
    writable_paths: list[str] = Field(default=[])
    readable_paths: list[str] = Field(default=[])


class GoogleStorageConstants(str, enum.Enum):
    AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
    TOKEN_URI = "https://oauth2.googleapis.com/token"
    AUTH_PROVIDER_CERT_URL = "https://www.googleapis.com/oauth2/v1/certs"
    UNIVERSE_DOMAIN = "googleapis.com"


class GoogleStorageApiKey(BaseModel):
    type: Literal["service_account"] = "service_account"
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str | None = Field(None)
    auth_uri: Literal[GoogleStorageConstants.AUTH_URI] = GoogleStorageConstants.AUTH_URI.value
    token_uri: Literal[GoogleStorageConstants.TOKEN_URI] = GoogleStorageConstants.TOKEN_URI.value
    auth_provider_x509_cert_url: Literal[GoogleStorageConstants.AUTH_PROVIDER_CERT_URL] = GoogleStorageConstants.AUTH_PROVIDER_CERT_URL.value
    universe_domain: Literal[GoogleStorageConstants.UNIVERSE_DOMAIN] = GoogleStorageConstants.UNIVERSE_DOMAIN.value

    @computed_field
    @property
    def client_x509_cert_url(self) -> str:
        return f"https://www.googleapis.com/robot/v1/metadata/x509/{self.client_email.replace('@', '%40')}"


class GoogleStorageConfiguration(StorageConfiguration):
    type: Literal["gs"] = "gs"
    is_local: Literal[False] = False
    bucket: str
    api_key: GoogleStorageApiKey | None = Field(default=None)

    @computed_field
    @property
    def is_anon_client(self) -> bool:
        return self.api_key is None

    @computed_field
    @property
    def credentials_file(self) -> str:
        if not self.is_anon_client:
            with tempfile.NamedTemporaryFile("w+", delete=False) as f:
                json.dump(self.api_key.model_dump(exclude_none=True, exclude_unset=True), f)
                f.close()
            credentials = f.name
        else:
            credentials = None
        return credentials


class HttpStorageConfiguration(StorageConfiguration):
    type: Literal["http"] = "http"
    is_local: Literal[False] = False
    headers: dict[str, str] = Field(default={})
    domain: str
    force_download: bool = Field(default=False)


class S3ApiKey(BaseModel):
    access_key: str
    secret_key: str


class S3StorageConfiguration(StorageConfiguration):
    type: Literal["s3"] = "s3"
    is_local: Literal[False] = False
    bucket: str
    endpoint: str
    api_key: S3ApiKey | None = Field(default=None)
    max_objects: int = Field(default=1000, description="Maximum number of objects to fetch when listing elements in a directory")

    @computed_field
    @property
    def is_anon_client(self) -> bool:
        return self.api_key is None


class HttpsStorageConfiguration(StorageConfiguration):
    type: Literal["https"] = "https"


AnyStorageConfiguration = Annotated[Union[FileStorageConfiguration, GoogleStorageConfiguration, HttpStorageConfiguration, HttpsStorageConfiguration, S3StorageConfiguration], Field(discriminator="type")]


class AccessManagerSettings(BaseModel):
    storages: list[AnyStorageConfiguration] = Field(title="List of configurations for the available storages")
    tmp_dir: str = Field(title="Temporary directory in which to write files that will be deleted")
