"""
Flask 애플리케이션 메인 파일
"""
import logging
import sys
from flask import Flask
from flask_cors import CORS
from config.settings import settings
from database.connection import db_manager
from database.redis_client import redis_manager
from database.opensearch_client import opensearch_manager
from api.routes import api_bp
from utils.logger import setup_logging

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Flask 애플리케이션 팩토리"""
    app = Flask(__name__)
    
    # CORS 설정
    CORS(app, resources={
        r"/api/*": {
            "origins": [f"http://localhost:{settings.FRONTEND_PORT}", f"http://127.0.0.1:{settings.FRONTEND_PORT}"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 블루프린트 등록
    app.register_blueprint(api_bp)
    
    return app


def initialize_services():
    """서비스 초기화"""
    logger.info("서비스 초기화 시작...")
    
    # 데이터베이스 연결 테스트
    if not db_manager.test_connection():
        logger.error("데이터베이스 연결 실패")
        sys.exit(1)
    
    # 테이블 생성
    db_manager.create_tables()
    
    # Redis 연결 테스트
    if not redis_manager.test_connection():
        logger.warning("Redis 연결 실패 - 캐시 기능이 비활성화됩니다")
    
    # OpenSearch 연결 테스트 및 인덱스 생성
    if opensearch_manager.test_connection():
        opensearch_manager.create_index()
    else:
        logger.warning("OpenSearch 연결 실패 - 검색 기능이 비활성화됩니다")
    
    logger.info("서비스 초기화 완료")


def main():
    """메인 함수"""
    try:
        # 서비스 초기화
        initialize_services()
        
        # Flask 앱 생성
        app = create_app()
        
        # 개발 서버 실행
        logger.info("Flask 서버 시작...")
        app.run(
            host='0.0.0.0',
            port=settings.BACKEND_PORT,
            debug=settings.DEBUG_MODE,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("서버 종료")
    except Exception as e:
        logger.error(f"서버 실행 오류: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()