from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")
    
    b2_key_id: str
    b2_application_key: str
    b2_bucket_name: str
    b2_endpoint: str
    openai_api_key: str
    elevenlabs_api_key: str
    gmi_cloud_api_key: str
    job_output_dir: str = "./output"
    app_env: str = "development"

settings = Settings()