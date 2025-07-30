"""
LLM 서비스 관리
"""
import logging
from typing import Optional, Dict, Any, List
from langchain.llms.base import LLM
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
import requests
from config.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 서비스 관리자"""
    
    def __init__(self):
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """LLM 초기화"""
        try:
            provider = settings.LLM_PROVIDER.lower()
            
            if provider == "openai" and settings.OPENAI_API_KEY:
                self.llm = ChatOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                    timeout=settings.LLM_TIMEOUT,
                    max_retries=settings.LLM_MAX_RETRIES
                )
                logger.info(f"OpenAI LLM 초기화 완료: {settings.OPENAI_MODEL}")
                
            elif provider == "google" and settings.GOOGLE_API_KEY:
                self.llm = ChatGoogleGenerativeAI(
                    google_api_key=settings.GOOGLE_API_KEY,
                    model=settings.GEMINI_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.LLM_MAX_TOKENS
                )
                logger.info(f"Google Gemini LLM 초기화 완료: {settings.GEMINI_MODEL}")
                
            elif provider == "ollama":
                self._initialize_ollama()
                
            elif provider == "deepinfra" and settings.DEEPINFRA_API_KEY:
                self._initialize_deepinfra()
                
            else:
                logger.warning("LLM 초기화 실패: API 키가 없거나 지원하지 않는 프로바이더")
                self.llm = None
                
        except Exception as e:
            logger.error(f"LLM 초기화 오류: {e}")
            self.llm = None
    
    def _initialize_ollama(self):
        """Ollama LLM 초기화"""
        try:
            from langchain_community.llms import Ollama
            
            self.llm = Ollama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                timeout=settings.LLM_TIMEOUT
            )
            logger.info(f"Ollama LLM 초기화 완료: {settings.OLLAMA_MODEL}")
            
        except ImportError:
            logger.error("Ollama를 사용하려면 langchain-community 패키지가 필요합니다")
            self.llm = None
        except Exception as e:
            logger.error(f"Ollama LLM 초기화 오류: {e}")
            self.llm = None
    
    def _initialize_deepinfra(self):
        """DeepInfra LLM 초기화"""
        try:
            self.llm = ChatOpenAI(
                api_key=settings.DEEPINFRA_API_KEY,
                base_url=settings.DEEPINFRA_BASE_URL,
                model=settings.DEEPINFRA_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                timeout=settings.LLM_TIMEOUT,
                max_retries=settings.LLM_MAX_RETRIES
            )
            logger.info(f"DeepInfra LLM 초기화 완료: {settings.DEEPINFRA_MODEL}")
            
        except Exception as e:
            logger.error(f"DeepInfra LLM 초기화 오류: {e}")
            self.llm = None
    
    def is_available(self) -> bool:
        """LLM 사용 가능 여부 확인"""
        return self.llm is not None
    
    def generate_response(self, messages: List[BaseMessage]) -> Optional[str]:
        """응답 생성"""
        if not self.llm:
            logger.warning("LLM이 초기화되지 않음")
            return None
        
        try:
            response = self.llm.invoke(messages)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            logger.error(f"LLM 응답 생성 오류: {e}")
            return None
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """감정 분석"""
        if not self.llm:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        
        system_prompt = """
        당신은 금융 앱 리뷰의 감정을 분석하는 전문가입니다.
        주어진 리뷰 텍스트를 분석하여 다음 형식으로 응답해주세요:
        
        감정: positive/negative/neutral 중 하나
        점수: -1.0(매우 부정) ~ 1.0(매우 긍정) 사이의 실수
        신뢰도: 0.0 ~ 1.0 사이의 실수
        
        응답 형식:
        감정: [감정]
        점수: [점수]
        신뢰도: [신뢰도]
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"리뷰 텍스트: {text}")
        ]
        
        try:
            response = self.generate_response(messages)
            if not response:
                return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
            
            # 응답 파싱
            result = {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
            
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('감정:'):
                    sentiment = line.split(':', 1)[1].strip().lower()
                    if sentiment in ['positive', 'negative', 'neutral']:
                        result['sentiment'] = sentiment
                elif line.startswith('점수:'):
                    try:
                        score = float(line.split(':', 1)[1].strip())
                        result['score'] = max(-1.0, min(1.0, score))
                    except ValueError:
                        pass
                elif line.startswith('신뢰도:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                        result['confidence'] = max(0.0, min(1.0, confidence))
                    except ValueError:
                        pass
            
            return result
            
        except Exception as e:
            logger.error(f"감정 분석 오류: {e}")
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
    
    def assign_department(self, text: str, departments: List[Dict[str, Any]]) -> Optional[str]:
        """부서 배정"""
        if not self.llm or not departments:
            return None
        
        dept_info = "\n".join([
            f"- {dept['name']}: {dept.get('description', '')} (키워드: {dept.get('keywords', [])})"
            for dept in departments
        ])
        
        system_prompt = f"""
        당신은 금융 앱 리뷰를 적절한 부서에 배정하는 전문가입니다.
        
        사용 가능한 부서:
        {dept_info}
        
        주어진 리뷰 내용을 분석하여 가장 적합한 부서 이름을 응답해주세요.
        부서 이름만 정확히 응답하세요.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"리뷰 내용: {text}")
        ]
        
        try:
            response = self.generate_response(messages)
            if response:
                # 응답에서 부서 이름 추출
                response = response.strip()
                for dept in departments:
                    if dept['name'] in response:
                        return dept['name']
            
            return None
            
        except Exception as e:
            logger.error(f"부서 배정 오류: {e}")
            return None


# 전역 LLM 서비스 인스턴스
llm_service = LLMService()