import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    google_api_key: Optional[str] = os.getenv("Google_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model_gemini: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", "storage"))

    @property
    def chroma_dir(self) -> Path:
        return self.storage_dir / "chroma"

    @property
    def docs_dir(self) -> Path:
        return self.storage_dir / "docs"

    def ensure_dirs(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
