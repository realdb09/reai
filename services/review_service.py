"""
리뷰 분석 서비스
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import Review, FinancialCompany, Department, AgentLog, SentimentEnum, PlatformEnum
from database.connection import db_manager
from database.redis_client import redis_manager
from database.opensearch_client import opensearch_manager
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ReviewService:
    """리뷰 분석 서비스"""
    
    def __init__(self):
        self.cache_prefix = "review_service"
    
    def create_review(self, review_data: Dict[str, Any]) -> Optional[Review]:
        """리뷰 생성"""
        try:
            with db_manager.get_session() as session:
                # 회사 존재 확인
                company = session.query(FinancialCompany).filter_by(
                    id=review_data['company_id']
                ).first()
                
                if not company:
                    logger.error(f"존재하지 않는 회사 ID: {review_data['company_id']}")
                    return None
                
                # 리뷰 생성
                review = Review(
                    company_id=review_data['company_id'],
                    content=review_data['content'],
                    rating=review_data.get('rating'),
                    review_date=review_data.get('review_date'),
                    platform=PlatformEnum(review_data['platform'])
                )
                
                session.add(review)
                session.flush()  # ID 생성을 위해 flush
                
                # 감정 분석 수행
                if llm_service.is_available():
                    sentiment_result = llm_service.analyze_sentiment(review.content)
                    review.sentiment = SentimentEnum(sentiment_result['sentiment'])
                    review.sentiment_score = sentiment_result['score']
                    
                    # 부서 배정
                    departments = self.get_departments(session)
                    if departments:
                        assigned_dept = llm_service.assign_department(
                            review.content, 
                            [dept.to_dict() for dept in departments]
                        )
                        if assigned_dept:
                            review.department_assigned = assigned_dept
                
                review.processed = True
                session.commit()
                
                # OpenSearch에 인덱싱
                self._index_review_to_opensearch(review)
                
                # 캐시 무효화
                self._invalidate_cache()
                
                logger.info(f"리뷰 생성 완료: {review.id}")
                return review
                
        except Exception as e:
            logger.error(f"리뷰 생성 오류: {e}")
            return None
    
    def get_reviews(self, company_id: Optional[int] = None, 
                   sentiment: Optional[str] = None,
                   department: Optional[str] = None,
                   limit: int = 50) -> List[Review]:
        """리뷰 목록 조회"""
        cache_key = f"{self.cache_prefix}:reviews:{company_id}:{sentiment}:{department}:{limit}"
        
        # 캐시 확인
        cached_result = redis_manager.get(cache_key)
        if cached_result:
            logger.debug("캐시에서 리뷰 목록 반환")
            return cached_result
        
        try:
            with db_manager.get_session() as session:
                query = session.query(Review)
                
                if company_id:
                    query = query.filter(Review.company_id == company_id)
                
                if sentiment:
                    query = query.filter(Review.sentiment == SentimentEnum(sentiment))
                
                if department:
                    query = query.filter(Review.department_assigned == department)
                
                reviews = query.order_by(Review.created_at.desc()).limit(limit).all()
                
                # 결과를 딕셔너리로 변환
                result = [review.to_dict() for review in reviews]
                
                # 캐시 저장
                redis_manager.set(cache_key, result)
                
                return result
                
        except Exception as e:
            logger.error(f"리뷰 목록 조회 오류: {e}")
            return []
    
    def search_reviews(self, query: str, size: int = 10) -> List[Dict[str, Any]]:
        """리뷰 검색"""
        try:
            # OpenSearch에서 검색
            results = opensearch_manager.search_reviews_by_content(query, size)
            
            if not results:
                logger.info(f"검색 결과 없음: {query}")
                return []
            
            logger.info(f"검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"리뷰 검색 오류: {e}")
            return []
    
    def get_sentiment_statistics(self, company_id: Optional[int] = None) -> Dict[str, Any]:
        """감정 통계 조회"""
        cache_key = f"{self.cache_prefix}:sentiment_stats:{company_id}"
        
        # 캐시 확인
        cached_result = redis_manager.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            with db_manager.get_session() as session:
                query = session.query(Review)
                
                if company_id:
                    query = query.filter(Review.company_id == company_id)
                
                total_count = query.count()
                
                if total_count == 0:
                    return {"total": 0, "positive": 0, "negative": 0, "neutral": 0}
                
                # 감정별 카운트
                positive_count = query.filter(Review.sentiment == SentimentEnum.POSITIVE).count()
                negative_count = query.filter(Review.sentiment == SentimentEnum.NEGATIVE).count()
                neutral_count = query.filter(Review.sentiment == SentimentEnum.NEUTRAL).count()
                
                result = {
                    "total": total_count,
                    "positive": positive_count,
                    "negative": negative_count,
                    "neutral": neutral_count,
                    "positive_ratio": positive_count / total_count,
                    "negative_ratio": negative_count / total_count,
                    "neutral_ratio": neutral_count / total_count
                }
                
                # 캐시 저장
                redis_manager.set(cache_key, result)
                
                return result
                
        except Exception as e:
            logger.error(f"감정 통계 조회 오류: {e}")
            return {"total": 0, "positive": 0, "negative": 0, "neutral": 0}
    
    def get_departments(self, session: Session) -> List[Department]:
        """부서 목록 조회"""
        try:
            return session.query(Department).all()
        except Exception as e:
            logger.error(f"부서 목록 조회 오류: {e}")
            return []
    
    def create_department(self, dept_data: Dict[str, Any]) -> Optional[Department]:
        """부서 생성"""
        try:
            with db_manager.get_session() as session:
                department = Department(
                    name=dept_data['name'],
                    description=dept_data.get('description'),
                    keywords=dept_data.get('keywords', [])
                )
                
                session.add(department)
                session.commit()
                
                # 캐시 무효화
                self._invalidate_cache()
                
                logger.info(f"부서 생성 완료: {department.name}")
                return department
                
        except Exception as e:
            logger.error(f"부서 생성 오류: {e}")
            return None
    
    def _index_review_to_opensearch(self, review: Review):
        """리뷰를 OpenSearch에 인덱싱"""
        try:
            document = {
                "company_id": review.company_id,
                "content": review.content,
                "rating": review.rating,
                "review_date": review.review_date.isoformat() if review.review_date else None,
                "platform": review.platform.value if review.platform else None,
                "sentiment": review.sentiment.value if review.sentiment else None,
                "sentiment_score": review.sentiment_score,
                "department_assigned": review.department_assigned,
                "created_at": review.created_at.isoformat() if review.created_at else None
            }
            
            opensearch_manager.index_document(str(review.id), document)
            
        except Exception as e:
            logger.error(f"OpenSearch 인덱싱 오류: {e}")
    
    def _invalidate_cache(self):
        """캐시 무효화"""
        try:
            pattern = f"{self.cache_prefix}:*"
            keys = redis_manager.keys(pattern)
            for key in keys:
                redis_manager.delete(key)
            logger.debug("리뷰 서비스 캐시 무효화 완료")
        except Exception as e:
            logger.error(f"캐시 무효화 오류: {e}")


# 전역 리뷰 서비스 인스턴스
review_service = ReviewService()