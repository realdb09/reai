"""
Redis 클라이언트 관리
"""
import json
import logging
from typing import Any, Optional, List
import redis
from redis.sentinel import Sentinel
from config.settings import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis 연결 관리자"""
    
    def __init__(self):
        self.sentinel = None
        self.redis_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Redis 클라이언트 초기화"""
        try:
            # Sentinel 설정
            self.sentinel = Sentinel(
                settings.redis_sentinel_hosts,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT
            )
            
            # Master 연결
            self.redis_client = self.sentinel.master_for(
                settings.REDIS_SENTINEL_SERVICE_NAME,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                password=settings.REDIS_PASSWORD,
                db=settings.REDIS_DB,
                decode_responses=True
            )
            
            logger.info("Redis 클라이언트 초기화 완료")
            
        except Exception as e:
            logger.warning(f"Redis Sentinel 연결 실패, 단일 Redis로 폴백: {e}")
            # Sentinel 실패 시 단일 Redis 연결
            try:
                host, port = settings.redis_sentinel_hosts[0]
                self.redis_client = redis.Redis(
                    host=host,
                    port=port,
                    password=settings.REDIS_PASSWORD,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT
                )
                logger.info("단일 Redis 연결 완료")
            except Exception as fallback_error:
                logger.error(f"Redis 연결 완전 실패: {fallback_error}")
                self.redis_client = None
    
    def test_connection(self) -> bool:
        """Redis 연결 테스트"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            logger.info("Redis 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"Redis 연결 테스트 실패: {e}")
            return False
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """값 저장"""
        if not self.redis_client:
            return False
        
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            ttl = ttl or settings.CACHE_TTL_SECONDS
            self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis SET 오류 [{key}]: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """값 조회"""
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            # JSON 파싱 시도
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logger.error(f"Redis GET 오류 [{key}]: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """값 삭제"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE 오류 [{key}]: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """키 존재 확인"""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS 오류 [{key}]: {e}")
            return False
    
    def keys(self, pattern: str = "*") -> List[str]:
        """키 목록 조회"""
        if not self.redis_client:
            return []
        
        try:
            return self.redis_client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis KEYS 오류 [{pattern}]: {e}")
            return []


# 전역 Redis 매니저 인스턴스
redis_manager = RedisManager()