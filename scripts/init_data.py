#!/usr/bin/env python3
"""
초기 데이터 생성 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime, timedelta
from database.connection import db_manager
from models.database import FinancialCompany, Department, Review, PlatformEnum
from utils.logger import setup_logging

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)


def create_sample_companies():
    """샘플 금융사 생성"""
    companies_data = [
        {
            'name': '카카오뱅크',
            'app_id': 'com.kakaobank.channel',
            'category': '인터넷은행'
        },
        {
            'name': '토스',
            'app_id': 'viva.republica.toss',
            'category': '핀테크'
        },
        {
            'name': '국민은행',
            'app_id': 'com.kbstar.kbbank',
            'category': '시중은행'
        },
        {
            'name': '신한은행',
            'app_id': 'com.shinhan.sbanking',
            'category': '시중은행'
        },
        {
            'name': '우리은행',
            'app_id': 'com.wooribank.smart',
            'category': '시중은행'
        }
    ]
    
    try:
        with db_manager.get_session() as session:
            for company_data in companies_data:
                # 중복 확인
                existing = session.query(FinancialCompany).filter_by(
                    app_id=company_data['app_id']
                ).first()
                
                if not existing:
                    company = FinancialCompany(**company_data)
                    session.add(company)
                    logger.info(f"금융사 생성: {company_data['name']}")
                else:
                    logger.info(f"금융사 이미 존재: {company_data['name']}")
            
            session.commit()
            logger.info("샘플 금융사 생성 완료")
            
    except Exception as e:
        logger.error(f"샘플 금융사 생성 오류: {e}")


def create_sample_departments():
    """샘플 부서 생성"""
    departments_data = [
        {
            'name': '고객서비스팀',
            'description': '고객 문의 및 불만 처리',
            'keywords': ['고객센터', '문의', '상담', '불만', '서비스']
        },
        {
            'name': '앱개발팀',
            'description': '모바일 앱 개발 및 유지보수',
            'keywords': ['앱', '버그', '오류', '업데이트', '기능', '화면']
        },
        {
            'name': '보안팀',
            'description': '보안 및 인증 관련 업무',
            'keywords': ['보안', '인증', '로그인', '비밀번호', '해킹', '안전']
        },
        {
            'name': '상품기획팀',
            'description': '금융상품 기획 및 관리',
            'keywords': ['상품', '금리', '수수료', '대출', '예금', '투자']
        },
        {
            'name': '마케팅팀',
            'description': '마케팅 및 프로모션',
            'keywords': ['이벤트', '혜택', '프로모션', '광고', '마케팅']
        }
    ]
    
    try:
        with db_manager.get_session() as session:
            for dept_data in departments_data:
                # 중복 확인
                existing = session.query(Department).filter_by(
                    name=dept_data['name']
                ).first()
                
                if not existing:
                    department = Department(**dept_data)
                    session.add(department)
                    logger.info(f"부서 생성: {dept_data['name']}")
                else:
                    logger.info(f"부서 이미 존재: {dept_data['name']}")
            
            session.commit()
            logger.info("샘플 부서 생성 완료")
            
    except Exception as e:
        logger.error(f"샘플 부서 생성 오류: {e}")


def create_sample_reviews():
    """샘플 리뷰 생성"""
    reviews_data = [
        {
            'content': '앱이 정말 편리하고 사용하기 쉬워요. 특히 송금 기능이 빠르고 간편합니다.',
            'rating': 5,
            'platform': PlatformEnum.GOOGLE_PLAY
        },
        {
            'content': '로그인이 자꾸 안되고 앱이 느려요. 개선이 필요합니다.',
            'rating': 2,
            'platform': PlatformEnum.APP_STORE
        },
        {
            'content': '고객센터 응답이 너무 늦어요. 문의한지 3일이 지났는데 답변이 없네요.',
            'rating': 1,
            'platform': PlatformEnum.GOOGLE_PLAY
        },
        {
            'content': '새로운 기능들이 계속 추가되어서 좋아요. 특히 가계부 기능이 유용합니다.',
            'rating': 4,
            'platform': PlatformEnum.APP_STORE
        },
        {
            'content': '보안이 강화되어서 안심이 되지만, 인증 과정이 너무 복잡해요.',
            'rating': 3,
            'platform': PlatformEnum.GOOGLE_PLAY
        }
    ]
    
    try:
        with db_manager.get_session() as session:
            # 첫 번째 회사 가져오기
            company = session.query(FinancialCompany).first()
            if not company:
                logger.error("샘플 리뷰 생성을 위한 회사가 없습니다")
                return
            
            for i, review_data in enumerate(reviews_data):
                review = Review(
                    company_id=company.id,
                    content=review_data['content'],
                    rating=review_data['rating'],
                    platform=review_data['platform'],
                    review_date=datetime.utcnow() - timedelta(days=i)
                )
                
                session.add(review)
                logger.info(f"리뷰 생성: {review_data['content'][:30]}...")
            
            session.commit()
            logger.info("샘플 리뷰 생성 완료")
            
    except Exception as e:
        logger.error(f"샘플 리뷰 생성 오류: {e}")


def main():
    """메인 함수"""
    logger.info("초기 데이터 생성 시작...")
    
    try:
        # 데이터베이스 연결 테스트
        if not db_manager.test_connection():
            logger.error("데이터베이스 연결 실패")
            sys.exit(1)
        
        # 테이블 생성
        db_manager.create_tables()
        
        # 샘플 데이터 생성
        create_sample_companies()
        create_sample_departments()
        create_sample_reviews()
        
        logger.info("초기 데이터 생성 완료")
        
    except Exception as e:
        logger.error(f"초기 데이터 생성 오류: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()