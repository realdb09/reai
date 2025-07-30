"""
OpenSearch 클라이언트 관리
"""
import json
import logging
from typing import Dict, List, Optional, Any
from opensearchpy import OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import NotFoundError, RequestError
import certifi
from config.settings import settings

logger = logging.getLogger(__name__)


class OpenSearchManager:
    """OpenSearch 연결 관리자"""
    
    def __init__(self):
        self.client = None
        self.index_name = "reviews-v1"
        self._initialize_client()
    
    def _initialize_client(self):
        """OpenSearch 클라이언트 초기화"""
        try:
            hosts = [settings.OPENSEARCH_HOSTS]
            
            self.client = OpenSearch(
                hosts=hosts,
                http_auth=(settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD),
                use_ssl=settings.OPENSEARCH_USE_SSL,
                verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
                ssl_assert_hostname=settings.OPENSEARCH_SSL_ASSERT_HOSTNAME,
                ssl_show_warn=settings.OPENSEARCH_SSL_SHOW_WARN,
                ca_certs=certifi.where(),
                connection_class=RequestsHttpConnection,
                timeout=settings.OPENSEARCH_TIMEOUT,
                max_retries=settings.OPENSEARCH_MAX_RETRIES,
                retry_on_timeout=settings.OPENSEARCH_RETRY_ON_TIMEOUT,
            )
            
            logger.info("OpenSearch 클라이언트 초기화 완료")
            
        except Exception as e:
            logger.error(f"OpenSearch 클라이언트 초기화 실패: {e}")
            self.client = None
    
    def test_connection(self) -> bool:
        """OpenSearch 연결 테스트"""
        if not self.client:
            return False
        
        try:
            info = self.client.info()
            logger.info(f"OpenSearch 연결 테스트 성공: {info.get('version', {}).get('number', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"OpenSearch 연결 테스트 실패: {e}")
            return False
    
    def create_index(self) -> bool:
        """인덱스 생성"""
        if not self.client:
            return False
        
        mappings = {
            "settings": {
                "index": {
                    "number_of_shards": 3,
                    "number_of_replicas": 1,
                    "analysis": {
                        "analyzer": {
                            "korean": {
                                "type": "custom",
                                "tokenizer": "standard",
                                "filter": ["lowercase"]
                            }
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "company_id": {"type": "long"},
                    "content": {"type": "text", "analyzer": "korean"},
                    "rating": {"type": "byte"},
                    "review_date": {"type": "date"},
                    "platform": {"type": "keyword"},
                    "sentiment": {"type": "keyword"},
                    "sentiment_score": {"type": "float"},
                    "department_assigned": {"type": "keyword"},
                    "created_at": {"type": "date"}
                }
            }
        }
        
        try:
            if self.client.indices.exists(index=self.index_name):
                logger.info(f"인덱스 {self.index_name} 이미 존재")
                return True
            
            response = self.client.indices.create(
                index=self.index_name,
                body=mappings
            )
            logger.info(f"인덱스 {self.index_name} 생성 완료: {response}")
            return True
            
        except Exception as e:
            logger.error(f"인덱스 생성 실패: {e}")
            return False
    
    def index_document(self, doc_id: str, document: Dict[str, Any]) -> bool:
        """문서 인덱싱"""
        if not self.client:
            return False
        
        try:
            response = self.client.index(
                index=self.index_name,
                id=doc_id,
                body=document
            )
            logger.debug(f"문서 인덱싱 완료 [{doc_id}]: {response.get('result')}")
            return True
            
        except Exception as e:
            logger.error(f"문서 인덱싱 실패 [{doc_id}]: {e}")
            return False
    
    def search_documents(self, query: Dict[str, Any], size: int = 10) -> List[Dict[str, Any]]:
        """문서 검색"""
        if not self.client:
            return []
        
        try:
            response = self.client.search(
                index=self.index_name,
                body=query,
                size=size
            )
            
            hits = response.get('hits', {}).get('hits', [])
            results = []
            
            for hit in hits:
                result = hit['_source']
                result['_id'] = hit['_id']
                result['_score'] = hit['_score']
                results.append(result)
            
            logger.debug(f"검색 완료: {len(results)}개 문서 발견")
            return results
            
        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            return []
    
    def search_reviews_by_content(self, content: str, size: int = 10) -> List[Dict[str, Any]]:
        """리뷰 내용으로 검색"""
        query = {
            "query": {
                "match": {
                    "content": {
                        "query": content,
                        "analyzer": "korean"
                    }
                }
            },
            "sort": [
                {"_score": {"order": "desc"}},
                {"created_at": {"order": "desc"}}
            ]
        }
        
        return self.search_documents(query, size)
    
    def search_reviews_by_sentiment(self, sentiment: str, size: int = 10) -> List[Dict[str, Any]]:
        """감정별 리뷰 검색"""
        query = {
            "query": {
                "term": {
                    "sentiment": sentiment
                }
            },
            "sort": [
                {"sentiment_score": {"order": "desc"}},
                {"created_at": {"order": "desc"}}
            ]
        }
        
        return self.search_documents(query, size)
    
    def delete_document(self, doc_id: str) -> bool:
        """문서 삭제"""
        if not self.client:
            return False
        
        try:
            response = self.client.delete(
                index=self.index_name,
                id=doc_id
            )
            logger.debug(f"문서 삭제 완료 [{doc_id}]: {response.get('result')}")
            return True
            
        except NotFoundError:
            logger.warning(f"삭제할 문서를 찾을 수 없음: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"문서 삭제 실패 [{doc_id}]: {e}")
            return False


# 전역 OpenSearch 매니저 인스턴스
opensearch_manager = OpenSearchManager()