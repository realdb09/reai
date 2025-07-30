"""
Flask API 라우트 정의
"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from typing import Dict, Any
from services.review_service import review_service
from models.database import FinancialCompany
from database.connection import db_manager
from services.autogen_service import autogen_service
from services.monitoring_service import monitoring_service

logger = logging.getLogger(__name__)

# Blueprint 생성
api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


@api_bp.route('/companies', methods=['GET'])
def get_companies():
    """금융사 목록 조회"""
    try:
        with db_manager.get_session() as session:
            companies = session.query(FinancialCompany).all()
            return jsonify({
                'success': True,
                'data': [company.to_dict() for company in companies]
            })
    except Exception as e:
        logger.error(f"금융사 목록 조회 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/companies', methods=['POST'])
def create_company():
    """금융사 생성"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name') or not data.get('app_id'):
            return jsonify({
                'success': False,
                'error': 'name과 app_id는 필수입니다'
            }), 400
        
        with db_manager.get_session() as session:
            # 중복 확인
            existing = session.query(FinancialCompany).filter_by(
                app_id=data['app_id']
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'error': '이미 존재하는 app_id입니다'
                }), 400
            
            company = FinancialCompany(
                name=data['name'],
                app_id=data['app_id'],
                category=data.get('category')
            )
            
            session.add(company)
            session.commit()
            
            return jsonify({
                'success': True,
                'data': company.to_dict()
            }), 201
            
    except Exception as e:
        logger.error(f"금융사 생성 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/reviews', methods=['GET'])
def get_reviews():
    """리뷰 목록 조회"""
    try:
        company_id = request.args.get('company_id', type=int)
        sentiment = request.args.get('sentiment')
        department = request.args.get('department')
        limit = request.args.get('limit', default=50, type=int)
        
        reviews = review_service.get_reviews(
            company_id=company_id,
            sentiment=sentiment,
            department=department,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'data': reviews,
            'count': len(reviews)
        })
        
    except Exception as e:
        logger.error(f"리뷰 목록 조회 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/reviews', methods=['POST'])
def create_review():
    """리뷰 생성"""
    try:
        data = request.get_json()
        
        if not data or not data.get('company_id') or not data.get('content') or not data.get('platform'):
            return jsonify({
                'success': False,
                'error': 'company_id, content, platform은 필수입니다'
            }), 400
        
        # 날짜 파싱
        if data.get('review_date'):
            try:
                data['review_date'] = datetime.fromisoformat(data['review_date'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': '잘못된 날짜 형식입니다'
                }), 400
        
        review = review_service.create_review(data)
        
        if not review:
            return jsonify({
                'success': False,
                'error': '리뷰 생성에 실패했습니다'
            }), 500
        
        return jsonify({
            'success': True,
            'data': review.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"리뷰 생성 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/reviews/search', methods=['GET'])
def search_reviews():
    """리뷰 검색"""
    try:
        query = request.args.get('q')
        size = request.args.get('size', default=10, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': '검색어(q)는 필수입니다'
            }), 400
        
        results = review_service.search_reviews(query, size)
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"리뷰 검색 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/reviews/sentiment-stats', methods=['GET'])
def get_sentiment_statistics():
    """감정 통계 조회"""
    try:
        company_id = request.args.get('company_id', type=int)
        
        stats = review_service.get_sentiment_statistics(company_id)
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"감정 통계 조회 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/reviews/analyze', methods=['POST'])
def analyze_reviews_with_autogen():
    """AutoGen을 사용한 리뷰 분석"""
    try:
        data = request.get_json()
        
        if not data or not data.get('review_ids'):
            return jsonify({
                'success': False,
                'error': 'review_ids는 필수입니다'
            }), 400
        
        review_ids = data['review_ids']
        analysis_type = data.get('analysis_type', 'comprehensive')
        
        # 리뷰 데이터 조회
        with db_manager.get_session() as session:
            from models.database import Review
            reviews = session.query(Review).filter(Review.id.in_(review_ids)).all()
            review_data = [review.to_dict() for review in reviews]
        
        if not review_data:
            return jsonify({
                'success': False,
                'error': '분석할 리뷰를 찾을 수 없습니다'
            }), 404
        
        # AutoGen 분석 수행
        analysis_result = autogen_service.analyze_reviews(review_data, analysis_type)
        
        return jsonify({
            'success': True,
            'data': analysis_result
        })
        
    except Exception as e:
        logger.error(f"AutoGen 리뷰 분석 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/system/status', methods=['GET'])
def get_system_status():
    """시스템 상태 조회"""
    try:
        from database.redis_client import redis_manager
        from database.opensearch_client import opensearch_manager
        from services.llm_service import llm_service
        
        status = {
            'database': db_manager.test_connection(),
            'redis': redis_manager.test_connection(),
            'opensearch': opensearch_manager.test_connection(),
            'llm': llm_service.is_available(),
            'autogen': autogen_service.get_agent_status(),
            'monitoring': monitoring_service.get_monitoring_status(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': status
        })
        
    except Exception as e:
        logger.error(f"시스템 상태 조회 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/departments', methods=['GET'])
def get_departments():
    """부서 목록 조회"""
    try:
        with db_manager.get_session() as session:
            departments = review_service.get_departments(session)
            return jsonify({
                'success': True,
                'data': [dept.to_dict() for dept in departments]
            })
    except Exception as e:
        logger.error(f"부서 목록 조회 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/departments', methods=['POST'])
def create_department():
    """부서 생성"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'name은 필수입니다'
            }), 400
        
        department = review_service.create_department(data)
        
        if not department:
            return jsonify({
                'success': False,
                'error': '부서 생성에 실패했습니다'
            }), 500
        
        return jsonify({
            'success': True,
            'data': department.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"부서 생성 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500