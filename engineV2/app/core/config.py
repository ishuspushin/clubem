"""
Configuration Management with validation and environment variable loading.
Applies: Singleton Pattern, Pydantic for validation
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AppConfig(BaseModel):
    """Application-level configuration."""
    APP_NAME: str = "Group Order Extraction System"
    VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")
    LLM_PROVIDER: str = Field(default="gemini")
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Invalid log level: {v}')
        return v.upper()

    @validator('LLM_PROVIDER')
    def validate_llm_provider(cls, v):
        """Validate LLM provider."""
        valid_providers = ['gemini', 'openai']
        if v.lower() not in valid_providers:
            raise ValueError(f'Invalid LLM provider: {v}. Must be one of {valid_providers}')
        return v.lower()


class FlaskConfig(BaseModel):
    """Flask server configuration."""
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=5000, ge=1, le=65535)
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    MAX_CONTENT_LENGTH: int = Field(default=16777216)  # 16MB
    
    @validator('SECRET_KEY')
    def validate_secret_key(cls, v):
        """Warn if using default secret key."""
        if v == "your-secret-key-change-in-production":
            logger.warning("Using default SECRET_KEY - change for production!")
        return v


class GoogleAIConfig(BaseModel):
    """Google Gemini AI configuration."""
    GOOGLE_API_KEY: Optional[str] = None
    MODEL_NAME: str = Field(default="gemini-2.0-flash")
    TEMPERATURE: float = Field(default=0.1, ge=0.0, le=2.0)
    MAX_OUTPUT_TOKENS: int = Field(default=8192, ge=1)
    TOP_P: float = Field(default=0.95, ge=0.0, le=1.0)
    TOP_K: int = Field(default=40, ge=1)


class OpenAIConfig(BaseModel):
    """OpenAI configuration."""
    OPENAI_API_KEY: Optional[str] = None
    MODEL_NAME: str = Field(default="gpt-4o")
    TEMPERATURE: float = Field(default=0.1, ge=0.0, le=2.0)
    MAX_OUTPUT_TOKENS: int = Field(default=4096, ge=1)


class StorageConfig(BaseModel):
    """File storage configuration."""
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    UPLOAD_FOLDER: Path = Field(default=Path("uploads"))
    OUTPUT_FOLDER: Path = Field(default=Path("outputs"))
    ALLOWED_EXTENSIONS: set = Field(default={'pdf'})
    
    def __init__(self, **data):
        super().__init__(**data)
        # Create directories if they don't exist
        self.create_directories()
    
    def create_directories(self) -> None:
        """Create storage directories."""
        try:
            upload_path = self.BASE_DIR / self.UPLOAD_FOLDER
            output_path = self.BASE_DIR / self.OUTPUT_FOLDER
            
            upload_path.mkdir(parents=True, exist_ok=True)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep files
            (upload_path / '.gitkeep').touch(exist_ok=True)
            (output_path / '.gitkeep').touch(exist_ok=True)
            
            logger.info("Storage directories created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
    
    def get_upload_path(self) -> Path:
        """Get absolute upload directory path."""
        return self.BASE_DIR / self.UPLOAD_FOLDER
    
    def get_output_path(self) -> Path:
        """Get absolute output directory path."""
        return self.BASE_DIR / self.OUTPUT_FOLDER


class WorkflowConfig(BaseModel):
    """Workflow execution configuration."""
    MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    HUMAN_REVIEW_TIMEOUT: int = Field(default=300, ge=30)  # 5 minutes
    ENABLE_AUTO_RETRY: bool = Field(default=True)
    REQUIRE_HUMAN_REVIEW: bool = Field(default=True)
    BATCH_SIZE: int = Field(default=10, ge=1, le=100)


class PlatformConfig(BaseModel):
    """Platform-specific configuration."""
    SUPPORTED_PLATFORMS: list = Field(
        default=[
            'sharebite',
            'ezcater',
            'grubhub',
            'catercow',
            'clubfeast',
            'hungry',
            'forkable'
        ]
    )
    PLATFORM_DISPLAY_NAMES: Dict[str, str] = Field(
        default={
            'sharebite': 'Group Sharebite',
            'ezcater': 'Group EzCater',
            'grubhub': 'Group Grubhub',
            'catercow': 'Group CaterCow',
            'clubfeast': 'Group ClubFeast',
            'hungry': 'Group Hungry',
            'forkable': 'Group Forkable'
        }
    )


class Config(BaseSettings):
    """
    Main configuration class using Singleton pattern.
    
    Design Pattern: Singleton
    """
    _instance: Optional['Config'] = None
    
    # Sub-configurations
    app: AppConfig = Field(default_factory=AppConfig)
    flask: FlaskConfig = Field(default_factory=FlaskConfig)
    google_ai: GoogleAIConfig = Field(default_factory=GoogleAIConfig)
    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    platform: PlatformConfig = Field(default_factory=PlatformConfig)
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"
    
    @classmethod
    def load_from_env(cls) -> 'Config':
        """
        Load configuration from environment variables.
        
        Returns:
            Config instance
        """
        try:
            # Load environment variables
            google_api_key = os.getenv('GOOGLE_API_KEY', '')
            openai_api_key = os.getenv('OPENAI_API_KEY', '')
            llm_provider = os.getenv('LLM_PROVIDER', 'gemini').lower()
            
            # Basic validation: ensure the selected provider has an API key
            if llm_provider == 'gemini' and not google_api_key:
                logger.warning("LLM_PROVIDER is set to 'gemini' but GOOGLE_API_KEY is missing")
            elif llm_provider == 'openai' and not openai_api_key:
                logger.warning("LLM_PROVIDER is set to 'openai' but OPENAI_API_KEY is missing")

            config = cls(
                google_ai=GoogleAIConfig(
                    GOOGLE_API_KEY=google_api_key,
                    MODEL_NAME=os.getenv('GOOGLE_MODEL_NAME', 'gemini-2.0-flash'),
                    TEMPERATURE=float(os.getenv('TEMPERATURE', '0.1')),
                    MAX_OUTPUT_TOKENS=int(os.getenv('MAX_OUTPUT_TOKENS', '8192'))
                ),
                openai=OpenAIConfig(
                    OPENAI_API_KEY=openai_api_key,
                    MODEL_NAME=os.getenv('OPENAI_MODEL_NAME', 'gpt-4o'),
                    TEMPERATURE=float(os.getenv('TEMPERATURE', '0.1')),
                    MAX_OUTPUT_TOKENS=int(os.getenv('MAX_OUTPUT_TOKENS', '4096'))
                ),
                flask=FlaskConfig(
                    HOST=os.getenv('FLASK_HOST', '0.0.0.0'),
                    PORT=int(os.getenv('FLASK_PORT', '5000')),
                    SECRET_KEY=os.getenv('SECRET_KEY', 'your-secret-key-change-in-production'),
                    MAX_CONTENT_LENGTH=int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))
                ),
                app=AppConfig(
                    DEBUG=os.getenv('FLASK_ENV', 'production') == 'development',
                    LOG_LEVEL=os.getenv('LOG_LEVEL', 'INFO'),
                    LLM_PROVIDER=llm_provider
                ),
                workflow=WorkflowConfig(
                    MAX_RETRIES=int(os.getenv('MAX_RETRIES', '3')),
                    HUMAN_REVIEW_TIMEOUT=int(os.getenv('HUMAN_REVIEW_TIMEOUT', '300')),
                    REQUIRE_HUMAN_REVIEW=os.getenv('REQUIRE_HUMAN_REVIEW', 'true').lower() == 'true'
                )
            )
            
            # Set singleton instance
            cls._instance = config
            return config
            
        except Exception as e:
            logger.error(f"Configuration loading failed: {e}")
            raise
    
    def validate_configuration(self) -> tuple[bool, list[str]]:
        """
        Validate entire configuration.
        
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        try:
            # Validate API key based on provider
            provider = self.app.LLM_PROVIDER
            if provider == 'gemini' and not self.google_ai.GOOGLE_API_KEY:
                errors.append("GOOGLE_API_KEY is not set but required for Gemini")
            elif provider == 'openai' and not self.openai.OPENAI_API_KEY:
                errors.append("OPENAI_API_KEY is not set but required for OpenAI")
            
            # Validate directories
            if not self.storage.get_upload_path().exists():
                errors.append("Upload directory does not exist")
            
            if not self.storage.get_output_path().exists():
                errors.append("Output directory does not exist")
            
            # Validate platforms
            if not self.platform.SUPPORTED_PLATFORMS:
                errors.append("No supported platforms configured")
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info("Configuration validation passed")
            else:
                logger.warning(f"Configuration validation failed: {errors}")
            
            return is_valid, errors
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return False, [str(e)]
    
    def get_platform_display_name(self, platform_key: str) -> str:
        """Get display name for platform."""
        return self.platform.PLATFORM_DISPLAY_NAMES.get(
            platform_key,
            platform_key.title()
        )
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.storage.ALLOWED_EXTENSIONS
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'app': self.app.dict(),
            'flask': {
                **self.flask.dict(),
                'SECRET_KEY': '***hidden***'  # Don't expose secret
            },
            'google_ai': {
                **self.google_ai.dict(),
                'GOOGLE_API_KEY': '***hidden***' if self.google_ai.GOOGLE_API_KEY else None
            },
            'openai': {
                **self.openai.dict(),
                'OPENAI_API_KEY': '***hidden***' if self.openai.OPENAI_API_KEY else None
            },
            'storage': {
                'UPLOAD_FOLDER': str(self.storage.UPLOAD_FOLDER),
                'OUTPUT_FOLDER': str(self.storage.OUTPUT_FOLDER),
                'ALLOWED_EXTENSIONS': list(self.storage.ALLOWED_EXTENSIONS)
            },
            'workflow': self.workflow.dict(),
            'platform': self.platform.dict()
        }
    
    # Convenience properties for backward compatibility
    @property
    def GOOGLE_API_KEY(self) -> str:
        return self.google_ai.GOOGLE_API_KEY
    
    @property
    def MODEL_NAME(self) -> str:
        return self.google_ai.MODEL_NAME
    
    @property
    def HUMAN_REVIEW_TIMEOUT(self) -> int:
        return self.workflow.HUMAN_REVIEW_TIMEOUT
    
    @property
    def UPLOAD_FOLDER(self) -> str:
        return str(self.storage.UPLOAD_FOLDER)
    
    @property
    def OUTPUT_FOLDER(self) -> str:
        return str(self.storage.OUTPUT_FOLDER)


# Global configuration instance
def get_config() -> Config:
    """Get or create global configuration instance."""
    return Config.load_from_env()
