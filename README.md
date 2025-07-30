# 금융사 앱 리뷰 분석 시스템

Python 기반의 금융사 모바일 앱 리뷰 수집 및 분석 시스템입니다.

## 주요 기능

- **리뷰 수집 및 저장**: 금융사 앱 리뷰 데이터 관리
- **감정 분석**: LLM을 활용한 리뷰 감정 분석 (긍정/부정/중립)
- **부서 자동 배정**: 리뷰 내용 기반 담당 부서 자동 배정
- **검색 및 인덱싱**: OpenSearch를 통한 고성능 리뷰 검색
- **캐싱**: Redis를 통한 성능 최적화
- **REST API**: Flask 기반 RESTful API 제공

## 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Web     │    │   Flask API     │    │   Database      │
│   (Port 2300)   │◄──►│   (Port 2400)   │◄──►│   MariaDB       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   LLM Service   │    │   OpenSearch    │
                       │   (감정분석)     │    │   (검색엔진)     │
                       └─────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis Cache   │    │   Logging       │
                       │   (캐시)        │    │   (모니터링)     │
                       └─────────────────┘    └─────────────────┘
```

## 설치 및 실행

### 1. 환경 설정

```bash
# Python 가상환경 생성 (Python 3.10.18 권장)
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집하여 필요한 값들 설정
# - 데이터베이스 연결 정보
# - LLM API 키 (OpenAI, Google 등)
# - Redis, OpenSearch 연결 정보
```

### 3. 데이터베이스 설정

MariaDB 설치 및 데이터베이스 생성:

```sql
CREATE DATABASE reai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'reai_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON reai.* TO 'reai_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. 초기 데이터 생성

```bash
# 샘플 데이터 생성
python scripts/init_data.py
```

### 5. 서버 실행

```bash
# Flask 서버 실행
python app.py
```

서버가 성공적으로 시작되면 `http://localhost:2400`에서 API에 접근할 수 있습니다.

### 6. API 테스트

```bash
# API 테스트 실행
python scripts/test_api.py
```

## API 엔드포인트

### 헬스 체크
- `GET /api/health` - 서버 상태 확인

### 금융사 관리
- `GET /api/companies` - 금융사 목록 조회
- `POST /api/companies` - 금융사 생성

### 리뷰 관리
- `GET /api/reviews` - 리뷰 목록 조회
- `POST /api/reviews` - 리뷰 생성
- `GET /api/reviews/search` - 리뷰 검색
- `GET /api/reviews/sentiment-stats` - 감정 통계 조회

### 부서 관리
- `GET /api/departments` - 부서 목록 조회
- `POST /api/departments` - 부서 생성

## 사용 예시

### 1. 금융사 생성

```bash
curl -X POST http://localhost:2400/api/companies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "카카오뱅크",
    "app_id": "com.kakaobank.channel",
    "category": "인터넷은행"
  }'
```

### 2. 리뷰 생성

```bash
curl -X POST http://localhost:2400/api/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "content": "앱이 정말 편리하고 사용하기 쉬워요!",
    "rating": 5,
    "platform": "google_play"
  }'
```

### 3. 리뷰 검색

```bash
curl "http://localhost:2400/api/reviews/search?q=편리&size=10"
```

### 4. 감정 통계 조회

```bash
curl "http://localhost:2400/api/reviews/sentiment-stats?company_id=1"
```

## 주요 구성 요소

### 1. 데이터베이스 모델
- `FinancialCompany`: 금융사 정보
- `Review`: 리뷰 데이터
- `Department`: 부서 정보
- `AgentLog`: 에이전트 처리 로그

### 2. 서비스 레이어
- `LLMService`: LLM 기반 감정 분석 및 부서 배정
- `ReviewService`: 리뷰 관리 및 분석 로직

### 3. 데이터베이스 연결
- `DatabaseManager`: MariaDB 연결 관리
- `RedisManager`: Redis 캐시 관리
- `OpenSearchManager`: OpenSearch 검색 엔진 관리

## 설정 옵션

### LLM 설정
- OpenAI GPT-4
- Google Gemini
- Ollama (로컬 모델)

### 캐시 설정
- Redis Sentinel 지원
- 캐시 TTL 설정 가능
- 자동 캐시 무효화

### 검색 설정
- OpenSearch 한국어 분석기 지원
- 실시간 인덱싱
- 복합 검색 쿼리 지원

## 로깅 및 모니터링

- 구조화된 로깅 (structlog)
- 로그 레벨 설정 가능
- 성능 메트릭 수집
- 에러 추적 및 알림

## 보안 고려사항

- API 키 환경 변수 관리
- 데이터베이스 연결 암호화
- CORS 설정
- 입력 데이터 검증

## 성능 최적화

- 데이터베이스 연결 풀링
- Redis 캐싱
- OpenSearch 인덱싱
- 비동기 처리 지원

## 문제 해결

### 1. 데이터베이스 연결 오류
- MariaDB 서버 실행 상태 확인
- 연결 정보 (.env) 확인
- 방화벽 설정 확인

### 2. LLM API 오류
- API 키 유효성 확인
- 네트워크 연결 확인
- 사용량 한도 확인

### 3. Redis 연결 오류
- Redis 서버 실행 상태 확인
- Sentinel 설정 확인 (사용 시)

### 4. OpenSearch 연결 오류
- OpenSearch 서버 실행 상태 확인
- SSL 인증서 설정 확인
- 사용자 권한 확인

## 라이선스

MIT License

## 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 지원

문의사항이나 버그 리포트는 GitHub Issues를 통해 제출해 주세요.