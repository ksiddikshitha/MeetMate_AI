from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SERVER_DIR = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    groq_api_key: str = ''
    groq_model: str = 'llama-3.3-70b-versatile'
    demo_mode: bool = False
    database_url: str = 'sqlite:///./meetmate.db'
    frontend_origin: str = 'http://localhost:5173,http://localhost:5174,http://127.0.0.1:5174'
    transcript_max_chars: int = 100000
    model_config = SettingsConfigDict(env_file=SERVER_DIR / '.env', extra='ignore')

    @property
    def has_groq_api_key(self) -> bool:
        key = self.groq_api_key.strip()
        return bool(key and key.lower() not in {'your_groq_api_key_here', 'your_groq_api_key', 'replace_me', 'changeme'})

settings = Settings()

