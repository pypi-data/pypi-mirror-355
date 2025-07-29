import logging

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import keyring

load_dotenv()
KEYRING_USERNAME = "user"

class Settings(BaseSettings):
    # Class variable to persist dev mode across instances
    _dev_mode_override: bool = False
    
    service_name: str = "CoDatascientist"
    api_key: SecretStr = ""
    log_level: int = logging.ERROR
    host: str = "localhost"
    port: int = 8001
    wait_time_between_checks_seconds: int = 10
    co_datascientist_backend_url: str = "https://172.208.104.249:8443"
    co_datascientist_backend_url_dev: str = "http://localhost:8000"
    verify_ssl: bool = False  # Set to False for self-signed certificates
    dev_mode: bool = False  # Set to True to use local backend
    
    class Config:
        env_prefix = "CO_DATASCIENTIST_"  # Allow environment variables with this prefix
    
    @property
    def backend_url(self) -> str:
        """Return the appropriate backend URL based on dev_mode setting"""
        # Check class variable first, then instance variable
        is_dev_mode = Settings._dev_mode_override or self.dev_mode
        if is_dev_mode:
            return self.co_datascientist_backend_url_dev
        return self.co_datascientist_backend_url
    
    @property 
    def effective_dev_mode(self) -> bool:
        """Return the effective dev mode considering both class and instance variables"""
        return Settings._dev_mode_override or self.dev_mode
    
    def enable_dev_mode(self):
        """Enable development mode to use local backend"""
        Settings._dev_mode_override = True
        self.dev_mode = True
        print(f"Development mode enabled. Using local backend: {self.co_datascientist_backend_url_dev}")
    
    def disable_dev_mode(self):
        """Disable development mode to use production backend"""
        Settings._dev_mode_override = False
        self.dev_mode = False
        print(f"Development mode disabled. Using production backend: {self.co_datascientist_backend_url}")

    def get_api_key(self):
        token = keyring.get_password(self.service_name, KEYRING_USERNAME)
        if not token:
            token = input("paste your api key: ").strip()
            keyring.set_password(self.service_name, KEYRING_USERNAME, token)
        self.api_key = SecretStr(token)

    def delete_api_key(self):
        keyring.delete_password(self.service_name, KEYRING_USERNAME)

settings = Settings()
