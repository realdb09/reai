"""
데이터베이스 연결 관리
"""
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from config.settings import settings
from models.database import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """데이터베이스 연결 관리자"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """데이터베이스 엔진 초기화"""
        try:
            self.engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_size=settings.DB_CONNECTION_POOL_SIZE,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=settings.DEBUG_MODE
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info("데이터베이스 엔진 초기화 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 엔진 초기화 실패: {e}")
            raise
    
    def create_tables(self):
        """테이블 생성"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("데이터베이스 테이블 생성 완료")
        except Exception as e:
            logger.error(f"테이블 생성 실패: {e}")
            raise
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("데이터베이스 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return False
    
    @contextmanager
    def get_session(self):
        """데이터베이스 세션 컨텍스트 매니저"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"데이터베이스 세션 오류: {e}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """직접 세션 반환 (수동 관리 필요)"""
        return self.SessionLocal()


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()