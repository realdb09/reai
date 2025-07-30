"""
AutoGen 멀티 에이전트 서비스
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from config.settings import settings

logger = logging.getLogger(__name__)

try:
    import autogen
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen 패키지가 설치되지 않았습니다. 멀티 에이전트 기능이 비활성화됩니다.")


class AutoGenService:
    """AutoGen 멀티 에이전트 서비스"""
    
    def __init__(self):
        self.enabled = settings.AUTOGEN_ENABLED and AUTOGEN_AVAILABLE
        self.agents = {}
        self.group_chats = {}
        
        if self.enabled:
            self._initialize_agents()
    
    def _initialize_agents(self):
        """에이전트 초기화"""
        if not AUTOGEN_AVAILABLE:
            return
        
        try:
            # LLM 설정
            llm_config = self._get_llm_config()
            
            # 금융 분석 에이전트
            self.agents['financial_analyst'] = autogen.AssistantAgent(
                name="financial_analyst",
                system_message="""
                당신은 금융 전문 분석가입니다. 
                금융사 앱 리뷰를 분석하여 다음을 수행합니다:
                1. 금융 상품 관련 이슈 식별
                2. 고객 만족도 분석
                3. 경쟁사 대비 강약점 분석
                4. 개선 방안 제시
                """,
                llm_config=llm_config
            )
            
            # 고객 서비스 에이전트
            self.agents['customer_service'] = autogen.AssistantAgent(
                name="customer_service",
                system_message="""
                당신은 고객 서비스 전문가입니다.
                고객 리뷰를 분석하여 다음을 수행합니다:
                1. 고객 불만사항 분류
                2. 긴급도 평가
                3. 대응 방안 제시
                4. 고객 만족도 개선 방안 제안
                """,
                llm_config=llm_config
            )
            
            # 기술 분석 에이전트
            self.agents['tech_analyst'] = autogen.AssistantAgent(
                name="tech_analyst",
                system_message="""
                당신은 기술 분석 전문가입니다.
                앱 관련 기술적 이슈를 분석하여 다음을 수행합니다:
                1. 기술적 문제 식별 및 분류
                2. 버그 및 성능 이슈 분석
                3. 기술적 개선 방안 제시
                4. 개발 우선순위 제안
                """,
                llm_config=llm_config
            )
            
            # 사용자 프록시 에이전트
            self.agents['user_proxy'] = autogen.UserProxyAgent(
                name="user_proxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=settings.AUTOGEN_MAX_ROUND,
                code_execution_config={
                    "work_dir": "autogen_workspace",
                    "use_docker": False
                } if settings.AUTOGEN_CODE_EXECUTION else False
            )
            
            # 그룹 채팅 설정
            self._setup_group_chats()
            
            logger.info("AutoGen 에이전트 초기화 완료")
            
        except Exception as e:
            logger.error(f"AutoGen 에이전트 초기화 오류: {e}")
            self.enabled = False
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """LLM 설정 반환"""
        config = {
            "timeout": settings.LLM_TIMEOUT,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }
        
        if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            config.update({
                "config_list": [{
                    "model": settings.OPENAI_MODEL,
                    "api_key": settings.OPENAI_API_KEY,
                }]
            })
        elif settings.LLM_PROVIDER == "google" and settings.GOOGLE_API_KEY:
            config.update({
                "config_list": [{
                    "model": settings.GEMINI_MODEL,
                    "api_key": settings.GOOGLE_API_KEY,
                    "api_type": "google"
                }]
            })
        
        return config
    
    def _setup_group_chats(self):
        """그룹 채팅 설정"""
        if not AUTOGEN_AVAILABLE:
            return
        
        try:
            # 금융 분석 그룹
            finance_agents = [
                self.agents['user_proxy'],
                self.agents['financial_analyst'],
                self.agents['customer_service']
            ]
            
            self.group_chats['finance'] = autogen.GroupChat(
                agents=finance_agents,
                messages=[],
                max_round=settings.AUTOGEN_MAX_ROUND
            )
            
            # 기술 분석 그룹
            tech_agents = [
                self.agents['user_proxy'],
                self.agents['tech_analyst'],
                self.agents['customer_service']
            ]
            
            self.group_chats['tech'] = autogen.GroupChat(
                agents=tech_agents,
                messages=[],
                max_round=settings.AUTOGEN_MAX_ROUND
            )
            
        except Exception as e:
            logger.error(f"그룹 채팅 설정 오류: {e}")
    
    def analyze_reviews(self, reviews: List[Dict[str, Any]], 
                       analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """리뷰 분석 수행"""
        if not self.enabled:
            return {"error": "AutoGen이 비활성화되어 있습니다"}
        
        try:
            # 리뷰 데이터 준비
            review_text = self._prepare_review_data(reviews)
            
            # 분석 유형에 따른 그룹 선택
            if analysis_type == "financial":
                group_chat = self.group_chats.get('finance')
            elif analysis_type == "technical":
                group_chat = self.group_chats.get('tech')
            else:
                group_chat = self.group_chats.get('finance')  # 기본값
            
            if not group_chat:
                return {"error": "적절한 분석 그룹을 찾을 수 없습니다"}
            
            # 그룹 채팅 매니저 생성
            manager = autogen.GroupChatManager(
                groupchat=group_chat,
                llm_config=self._get_llm_config()
            )
            
            # 분석 시작
            analysis_prompt = f"""
            다음 리뷰 데이터를 분석해주세요:
            
            {review_text}
            
            분석 요청사항:
            1. 주요 이슈 및 트렌드 식별
            2. 고객 만족도 평가
            3. 개선 방안 제시
            4. 우선순위 제안
            
            분석 결과를 JSON 형태로 정리해주세요.
            """
            
            # 대화 시작
            chat_result = self.agents['user_proxy'].initiate_chat(
                manager,
                message=analysis_prompt,
                max_turns=settings.AUTOGEN_MAX_ROUND
            )
            
            # 결과 처리
            result = self._process_chat_result(chat_result)
            
            return {
                "success": True,
                "analysis_type": analysis_type,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"리뷰 분석 오류: {e}")
            return {"error": str(e)}
    
    def _prepare_review_data(self, reviews: List[Dict[str, Any]]) -> str:
        """리뷰 데이터 준비"""
        review_summaries = []
        
        for review in reviews[:20]:  # 최대 20개 리뷰만 처리
            summary = f"""
            리뷰 ID: {review.get('id', 'N/A')}
            평점: {review.get('rating', 'N/A')}/5
            플랫폼: {review.get('platform', 'N/A')}
            감정: {review.get('sentiment', 'N/A')}
            내용: {review.get('content', '')[:200]}...
            """
            review_summaries.append(summary.strip())
        
        return "\n\n".join(review_summaries)
    
    def _process_chat_result(self, chat_result) -> Dict[str, Any]:
        """채팅 결과 처리"""
        try:
            # 마지막 메시지에서 결과 추출
            if hasattr(chat_result, 'chat_history'):
                messages = chat_result.chat_history
            else:
                messages = []
            
            # JSON 형태의 응답 찾기
            for message in reversed(messages):
                content = message.get('content', '')
                if '{' in content and '}' in content:
                    try:
                        # JSON 부분 추출 시도
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        json_str = content[start:end]
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        continue
            
            # JSON을 찾지 못한 경우 텍스트 응답 반환
            return {
                "analysis": "분석 완료",
                "messages": [msg.get('content', '') for msg in messages[-3:]]
            }
            
        except Exception as e:
            logger.error(f"채팅 결과 처리 오류: {e}")
            return {"error": "결과 처리 중 오류 발생"}
    
    def get_agent_status(self) -> Dict[str, Any]:
        """에이전트 상태 조회"""
        return {
            "enabled": self.enabled,
            "available": AUTOGEN_AVAILABLE,
            "agents": list(self.agents.keys()) if self.enabled else [],
            "group_chats": list(self.group_chats.keys()) if self.enabled else [],
            "settings": {
                "max_round": settings.AUTOGEN_MAX_ROUND,
                "timeout": settings.AUTOGEN_TIMEOUT,
                "code_execution": settings.AUTOGEN_CODE_EXECUTION,
                "parallel": settings.AUTOGEN_PARALLEL,
                "cache": settings.AUTOGEN_CACHE
            }
        }


# 전역 AutoGen 서비스 인스턴스
autogen_service = AutoGenService()