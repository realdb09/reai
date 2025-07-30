"""
데이터베이스 모델 정의
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Boolean, Float, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class PlatformEnum(enum.Enum):
    """플랫폼 열거형"""
    GOOGLE_PLAY = "google_play"
    APP_STORE = "app_store"


class SentimentEnum(enum.Enum):
    """감정 열거형"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class FinancialCompany(Base):
    """금융사 테이블"""
    __tablename__ = 'financial_companies'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    app_id = Column(String(100), nullable=False, unique=True)
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    reviews = relationship("Review", back_populates="company", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'app_id': self.app_id,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Review(Base):
    """리뷰 테이블"""
    __tablename__ = 'reviews'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_id = Column(BigInteger, ForeignKey('financial_companies.id'), nullable=False)
    content = Column(Text, nullable=False)
    rating = Column(Integer)  # 1-5
    review_date = Column(DateTime)
    platform = Column(Enum(PlatformEnum), nullable=False)
    sentiment = Column(Enum(SentimentEnum))
    sentiment_score = Column(Float)
    department_assigned = Column(String(100))
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    company = relationship("FinancialCompany", back_populates="reviews")
    agent_logs = relationship("AgentLog", back_populates="review", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'content': self.content,
            'rating': self.rating,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'platform': self.platform.value if self.platform else None,
            'sentiment': self.sentiment.value if self.sentiment else None,
            'sentiment_score': self.sentiment_score,
            'department_assigned': self.department_assigned,
            'processed': self.processed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Department(Base):
    """부서 테이블"""
    __tablename__ = 'departments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    keywords = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'keywords': self.keywords,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class AgentLog(Base):
    """에이전트 로그 테이블"""
    __tablename__ = 'agent_logs'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    review_id = Column(BigInteger, ForeignKey('reviews.id'), nullable=False)
    agent_type = Column(String(50))
    action = Column(String(100))
    result = Column(Text)
    processing_time = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    review = relationship("Review", back_populates="agent_logs")
    
    def to_dict(self):
        return {
            'id': self.id,
            'review_id': self.review_id,
            'agent_type': self.agent_type,
            'action': self.action,
            'result': self.result,
            'processing_time': self.processing_time,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }