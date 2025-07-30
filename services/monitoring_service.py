"""
모니터링 및 추적 서비스 (Langfuse, Phoenix)
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)

# Langfuse 관련 임포트
LANGFUSE_AVAILABLE = False
if settings.LANGFUSE_ENABLED:
    try:
        from langfuse import Langfuse
        LANGFUSE_AVAILABLE = True
    except ImportError:
        logger.warning("Langfuse 패키지가 설치되지 않았습니다")

# Phoenix 관련 임포트
PHOENIX_AVAILABLE = False
if settings.PHOENIX_ENABLED:
    try:
        import phoenix as px
        from phoenix.trace import using_project
        PHOENIX_AVAILABLE = True
    except ImportError:
        logger.warning("Phoenix 패키지가 설치되지 않았습니다")


class MonitoringService:
    """모니터링 및 추적 서비스"""
    
    def __init__(self):
        self.langfuse_client = None
        self.phoenix_client = None
        
        if settings.LANGFUSE_ENABLED and LANGFUSE_AVAILABLE:
            self._initialize_langfuse()
        
        if settings.PHOENIX_ENABLED and PHOENIX_AVAILABLE:
            self._initialize_phoenix()
    
    def _initialize_langfuse(self):
        """Langfuse 초기화"""
        try:
            if not all([settings.LANGFUSE_HOST, settings.LANGFUSE_PUBLIC_KEY, settings.LANGFUSE_SECRET_KEY]):
                logger.warning("Langfuse 설정이 불완전합니다")
                return
            
            self.langfuse_client = Langfuse(
                host=settings.LANGFUSE_HOST,
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                debug=settings.LANGFUSE_DEBUG,
                flush_at=settings.LANGFUSE_FLUSH_AT,
                flush_interval=settings.LANGFUSE_FLUSH_INTERVAL,
                timeout=settings.LANGFUSE_TIMEOUT
            )
            
            logger.info("Langfuse 클라이언트 초기화 완료")
            
        except Exception as e:
            logger.error(f"Langfuse 초기화 오류: {e}")
            self.langfuse_client = None
    
    def _initialize_phoenix(self):
        """Phoenix 초기화"""
        try:
            if settings.PHOENIX_ENDPOINT:
                # Phoenix 세션 시작
                px.launch_app(
                    host=settings.PHOENIX_ENDPOINT.split('://')[1].split(':')[0],
                    port=int(settings.PHOENIX_ENDPOINT.split(':')[-1])
                )
            
            logger.info("Phoenix 클라이언트 초기화 완료")
            
        except Exception as e:
            logger.error(f"Phoenix 초기화 오류: {e}")
            self.phoenix_client = None
    
    def trace_llm_call(self, 
                      model: str,
                      input_text: str,
                      output_text: str,
                      metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """LLM 호출 추적"""
        trace_id = None
        
        # Langfuse 추적
        if self.langfuse_client and settings.LANGFUSE_TRACE_LLM:
            try:
                trace = self.langfuse_client.trace(
                    name="llm_call",
                    metadata=metadata or {}
                )
                
                generation = trace.generation(
                    name=f"llm_{model}",
                    model=model,
                    input=input_text,
                    output=output_text,
                    metadata=metadata or {}
                )
                
                trace_id = trace.id
                logger.debug(f"Langfuse LLM 추적 완료: {trace_id}")
                
            except Exception as e:
                logger.error(f"Langfuse LLM 추적 오류: {e}")
        
        return trace_id
    
    def trace_agent_action(self,
                          agent_name: str,
                          action: str,
                          input_data: Dict[str, Any],
                          output_data: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """에이전트 액션 추적"""
        trace_id = None
        
        # Langfuse 추적
        if self.langfuse_client and settings.LANGFUSE_TRACE_AGENTS:
            try:
                trace = self.langfuse_client.trace(
                    name="agent_action",
                    metadata={
                        "agent_name": agent_name,
                        "action": action,
                        **(metadata or {})
                    }
                )
                
                span = trace.span(
                    name=f"agent_{agent_name}_{action}",
                    input=input_data,
                    output=output_data,
                    metadata=metadata or {}
                )
                
                trace_id = trace.id
                logger.debug(f"Langfuse 에이전트 추적 완료: {trace_id}")
                
            except Exception as e:
                logger.error(f"Langfuse 에이전트 추적 오류: {e}")
        
        return trace_id
    
    def trace_autogen_conversation(self,
                                 conversation_id: str,
                                 messages: list,
                                 metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """AutoGen 대화 추적"""
        trace_id = None
        
        # Langfuse 추적
        if self.langfuse_client and settings.LANGFUSE_TRACE_AUTOGEN:
            try:
                trace = self.langfuse_client.trace(
                    name="autogen_conversation",
                    metadata={
                        "conversation_id": conversation_id,
                        "message_count": len(messages),
                        **(metadata or {})
                    }
                )
                
                for i, message in enumerate(messages):
                    trace.span(
                        name=f"message_{i}",
                        input={"role": message.get("role", "unknown")},
                        output={"content": message.get("content", "")},
                        metadata={"message_index": i}
                    )
                
                trace_id = trace.id
                logger.debug(f"Langfuse AutoGen 추적 완료: {trace_id}")
                
            except Exception as e:
                logger.error(f"Langfuse AutoGen 추적 오류: {e}")
        
        return trace_id
    
    def log_performance_metrics(self,
                              operation: str,
                              duration: float,
                              success: bool,
                              metadata: Optional[Dict[str, Any]] = None):
        """성능 메트릭 로깅"""
        try:
            metrics = {
                "operation": operation,
                "duration_ms": duration * 1000,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
                **(metadata or {})
            }
            
            # Langfuse 메트릭
            if self.langfuse_client:
                self.langfuse_client.trace(
                    name="performance_metric",
                    metadata=metrics
                )
            
            # 로그 출력
            logger.info(f"성능 메트릭: {operation} - {duration:.3f}s - {'성공' if success else '실패'}")
            
        except Exception as e:
            logger.error(f"성능 메트릭 로깅 오류: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """모니터링 상태 조회"""
        return {
            "langfuse": {
                "enabled": settings.LANGFUSE_ENABLED,
                "available": LANGFUSE_AVAILABLE,
                "connected": self.langfuse_client is not None,
                "settings": {
                    "trace_llm": settings.LANGFUSE_TRACE_LLM,
                    "trace_agents": settings.LANGFUSE_TRACE_AGENTS,
                    "trace_autogen": settings.LANGFUSE_TRACE_AUTOGEN,
                    "debug": settings.LANGFUSE_DEBUG
                }
            },
            "phoenix": {
                "enabled": settings.PHOENIX_ENABLED,
                "available": PHOENIX_AVAILABLE,
                "connected": self.phoenix_client is not None,
                "settings": {
                    "trace_llm": settings.PHOENIX_TRACE_LLM,
                    "trace_embeddings": settings.PHOENIX_TRACE_EMBEDDINGS,
                    "trace_retrievals": settings.PHOENIX_TRACE_RETRIEVALS,
                    "collect_metrics": settings.PHOENIX_COLLECT_METRICS,
                    "sample_rate": settings.PHOENIX_SAMPLE_RATE
                }
            }
        }
    
    def flush_traces(self):
        """추적 데이터 플러시"""
        try:
            if self.langfuse_client:
                self.langfuse_client.flush()
                logger.debug("Langfuse 추적 데이터 플러시 완료")
        except Exception as e:
            logger.error(f"추적 데이터 플러시 오류: {e}")


# 전역 모니터링 서비스 인스턴스
monitoring_service = MonitoringService()