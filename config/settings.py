"""
애플리케이션 설정 관리
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Flask 설정
    DEBUG_MODE: bool = Field(default=False, env="DEBUG_MODE")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 서버 포트 설정
    BACKEND_PORT: int = Field(default=2400, env="BACKEND_PORT")
    FRONTEND_PORT: int = Field(default=2300, env="FRONTEND_PORT")
    
    # LLM 설정
    LLM_PROVIDER: str = Field(default="openai", env="LLM_PROVIDER")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4", env="OPENAI_MODEL")
    GOOGLE_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-pro", env="GEMINI_MODEL")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    OLLAMA_API_KEY: Optional[str] = Field(default=None, env="OLLAMA_API_KEY")
    OLLAMA_MODEL: str = Field(default="llama2", env="OLLAMA_MODEL")
    DEEPINFRA_API_KEY: Optional[str] = Field(default=None, env="DEEPINFRA_API_KEY")
    DEEPINFRA_MODEL: str = Field(default="meta-llama/Llama-2-70b-chat-hf", env="DEEPINFRA_MODEL")
    DEEPINFRA_BASE_URL: str = Field(default="https://api.deepinfra.com/v1/openai", env="DEEPINFRA_BASE_URL")
    LLM_TEMPERATURE: float = Field(default=0.0, env="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(default=4096, env="LLM_MAX_TOKENS")
    LLM_TIMEOUT: int = Field(default=60, env="LLM_TIMEOUT")
    LLM_MAX_RETRIES: int = Field(default=3, env="LLM_MAX_RETRIES")
    
    # Redis 설정
    REDIS_SENTINEL_HOSTS: str = Field(default="localhost:26379", env="REDIS_SENTINEL_HOSTS")
    REDIS_SENTINEL_SERVICE_NAME: str = Field(default="mymaster", env="REDIS_SENTINEL_SERVICE_NAME")
    REDIS_PASSWORD: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    REDIS_DB: int = Field(default=0, env="REDIS_DB")
    REDIS_SOCKET_TIMEOUT: int = Field(default=3, env="REDIS_SOCKET_TIMEOUT")
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=3, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    # OpenSearch 설정
    OPENSEARCH_HOSTS: str = Field(default="https://localhost:9200", env="OPENSEARCH_HOSTS")
    OPENSEARCH_USER: str = Field(default="admin", env="OPENSEARCH_USER")
    OPENSEARCH_PASSWORD: str = Field(default="admin", env="OPENSEARCH_PASSWORD")
    OPENSEARCH_USE_SSL: bool = Field(default=True, env="OPENSEARCH_USE_SSL")
    OPENSEARCH_VERIFY_CERTS: bool = Field(default=False, env="OPENSEARCH_VERIFY_CERTS")
    OPENSEARCH_SSL_ASSERT_HOSTNAME: bool = Field(default=False, env="OPENSEARCH_SSL_ASSERT_HOSTNAME")
    OPENSEARCH_SSL_SHOW_WARN: bool = Field(default=False, env="OPENSEARCH_SSL_SHOW_WARN")
    OPENSEARCH_TIMEOUT: int = Field(default=30, env="OPENSEARCH_TIMEOUT")
    OPENSEARCH_MAX_RETRIES: int = Field(default=3, env="OPENSEARCH_MAX_RETRIES")
    OPENSEARCH_RETRY_ON_TIMEOUT: bool = Field(default=True, env="OPENSEARCH_RETRY_ON_TIMEOUT")
    
    # MariaDB 설정
    MARIADB_HOST: str = Field(default="localhost", env="MARIADB_HOST")
    MARIADB_PORT: int = Field(default=3306, env="MARIADB_PORT")
    MARIADB_USER: str = Field(default="root", env="MARIADB_USER")
    MARIADB_PASSWORD: str = Field(default="password", env="MARIADB_PASSWORD")
    MARIADB_DATABASE: str = Field(default="reai", env="MARIADB_DATABASE")
    MARIADB_CHARSET: str = Field(default="utf8mb4", env="MARIADB_CHARSET")
    MARIADB_CONNECT_TIMEOUT: int = Field(default=5, env="MARIADB_CONNECT_TIMEOUT")
    MARIADB_READ_TIMEOUT: int = Field(default=30, env="MARIADB_READ_TIMEOUT")
    MARIADB_WRITE_TIMEOUT: int = Field(default=30, env="MARIADB_WRITE_TIMEOUT")
    
    # 데이터베이스 초기화 상태
    DB_INITIALIZED: bool = Field(default=False, env="DB_INITIALIZED")
    
    # AutoGen 설정
    AUTOGEN_ENABLED: bool = Field(default=True, env="AUTOGEN_ENABLED")
    AUTOGEN_FINANCE_GROUP: str = Field(default="finance", env="AUTOGEN_FINANCE_GROUP")
    AUTOGEN_TRAVEL_GROUP: str = Field(default="travel", env="AUTOGEN_TRAVEL_GROUP")
    AUTOGEN_BANKING_GROUP: str = Field(default="banking", env="AUTOGEN_BANKING_GROUP")
    AUTOGEN_MAX_ROUND: int = Field(default=8, env="AUTOGEN_MAX_ROUND")
    AUTOGEN_TIMEOUT: int = Field(default=900, env="AUTOGEN_TIMEOUT")
    AUTOGEN_CODE_EXECUTION: bool = Field(default=True, env="AUTOGEN_CODE_EXECUTION")
    AUTOGEN_HUMAN_FEEDBACK: bool = Field(default=False, env="AUTOGEN_HUMAN_FEEDBACK")
    AUTOGEN_PARALLEL: bool = Field(default=True, env="AUTOGEN_PARALLEL")
    AUTOGEN_CACHE: bool = Field(default=True, env="AUTOGEN_CACHE")
    
    # Langfuse 설정
    LANGFUSE_ENABLED: bool = Field(default=False, env="LANGFUSE_ENABLED")
    LANGFUSE_HOST: Optional[str] = Field(default=None, env="LANGFUSE_HOST")
    LANGFUSE_PUBLIC_KEY: Optional[str] = Field(default=None, env="LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: Optional[str] = Field(default=None, env="LANGFUSE_SECRET_KEY")
    LANGFUSE_DEBUG: bool = Field(default=False, env="LANGFUSE_DEBUG")
    LANGFUSE_TRACE_LLM: bool = Field(default=True, env="LANGFUSE_TRACE_LLM")
    LANGFUSE_TRACE_AGENTS: bool = Field(default=True, env="LANGFUSE_TRACE_AGENTS")
    LANGFUSE_TRACE_AUTOGEN: bool = Field(default=True, env="LANGFUSE_TRACE_AUTOGEN")
    LANGFUSE_FLUSH_AT: int = Field(default=100, env="LANGFUSE_FLUSH_AT")
    LANGFUSE_FLUSH_INTERVAL: int = Field(default=5, env="LANGFUSE_FLUSH_INTERVAL")
    LANGFUSE_TIMEOUT: int = Field(default=10, env="LANGFUSE_TIMEOUT")
    
    # Phoenix 설정
    PHOENIX_ENABLED: bool = Field(default=False, env="PHOENIX_ENABLED")
    PHOENIX_ENDPOINT: Optional[str] = Field(default=None, env="PHOENIX_ENDPOINT")
    PHOENIX_GRPC_ENDPOINT: Optional[str] = Field(default=None, env="PHOENIX_GRPC_ENDPOINT")
    PHOENIX_TRACE_LLM: bool = Field(default=True, env="PHOENIX_TRACE_LLM")
    PHOENIX_TRACE_EMBEDDINGS: bool = Field(default=True, env="PHOENIX_TRACE_EMBEDDINGS")
    PHOENIX_TRACE_RETRIEVALS: bool = Field(default=True, env="PHOENIX_TRACE_RETRIEVALS")
    PHOENIX_COLLECT_METRICS: bool = Field(default=True, env="PHOENIX_COLLECT_METRICS")
    PHOENIX_SAMPLE_RATE: float = Field(default=0.1, env="PHOENIX_SAMPLE_RATE")
    
    # 검색 API 키
    GOOGLE_SEARCH_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_SEARCH_API_KEY")
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = Field(default=None, env="GOOGLE_SEARCH_ENGINE_ID")
    NAVER_CLIENT_ID: Optional[str] = Field(default=None, env="NAVER_CLIENT_ID")
    NAVER_CLIENT_SECRET: Optional[str] = Field(default=None, env="NAVER_CLIENT_SECRET")
    DAUM_APP_KEY: Optional[str] = Field(default=None, env="DAUM_APP_KEY")
    
    # 공공 데이터 API 키
    BOK_API_KEY: Optional[str] = Field(default=None, env="BOK_API_KEY")
    FSS_API_KEY: Optional[str] = Field(default=None, env="FSS_API_KEY")
    KOREAEXIM_API_KEY: Optional[str] = Field(default=None, env="KOREAEXIM_API_KEY")
    KFTC_API_KEY: Optional[str] = Field(default=None, env="KFTC_API_KEY")
    KFTC_CLIENT_ID: Optional[str] = Field(default=None, env="KFTC_CLIENT_ID")
    KFTC_CLIENT_SECRET: Optional[str] = Field(default=None, env="KFTC_CLIENT_SECRET")
    MOLIT_API_KEY: Optional[str] = Field(default=None, env="MOLIT_API_KEY")
    KOREA_LAND_API_KEY: Optional[str] = Field(default=None, env="KOREA_LAND_API_KEY")
    KB_REAL_ESTATE_API_KEY: Optional[str] = Field(default=None, env="KB_REAL_ESTATE_API_KEY")
    
    # 데이터베이스 연결 풀 설정
    DB_CONNECTION_POOL_SIZE: int = Field(default=20, env="DB_CONNECTION_POOL_SIZE")
    
    # 캐시 설정
    CACHE_TTL_SECONDS: int = Field(default=300, env="CACHE_TTL_SECONDS")
    QUERY_TIMEOUT_SECONDS: int = Field(default=15, env="QUERY_TIMEOUT_SECONDS")
    CACHE_HIT_THRESHOLD: int = Field(default=3, env="CACHE_HIT_THRESHOLD")
    CACHE_EVICTION_POLICY: str = Field(default="LFU", env="CACHE_EVICTION_POLICY")
    PRELOAD_CACHE_ENABLED: bool = Field(default=True, env="PRELOAD_CACHE_ENABLED")
    
    # 테스트 설정
    TESTING_DATABASE_URL: Optional[str] = Field(default=None, env="TESTING_DATABASE_URL")
    
    @property
    def database_url(self) -> str:
        """MariaDB 연결 URL 생성"""
        return (
            f"mysql+pymysql://{self.MARIADB_USER}:{self.MARIADB_PASSWORD}"
            f"@{self.MARIADB_HOST}:{self.MARIADB_PORT}/{self.MARIADB_DATABASE}"
            f"?charset={self.MARIADB_CHARSET}"
            f"&connect_timeout={self.MARIADB_CONNECT_TIMEOUT}"
            f"&read_timeout={self.MARIADB_READ_TIMEOUT}"
            f"&write_timeout={self.MARIADB_WRITE_TIMEOUT}"
        )
    
    @property
    def redis_sentinel_hosts(self) -> List[tuple]:
        """Redis Sentinel 호스트 목록 파싱"""
        hosts = []
        for host_port in self.REDIS_SENTINEL_HOSTS.split(','):
            host, port = host_port.strip().split(':')
            hosts.append((host, int(port)))
        return hosts
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 전역 설정 인스턴스
settings = Settings()