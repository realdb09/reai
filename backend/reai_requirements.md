# 금융사 앱 리뷰 분석 시스템 요구사항

이 문서는 RHEL8 환경의 `/app/prod/reai` 경로에서 **conda env `bank`(Python 3.10.18)**를 사용해 개발할 때 필요한 환경 변수 설정과 초기 객체(데이터베이스·검색 인덱스) 생성 절차를 상세히 정의한다.

## 1. 프로젝트 구조 및 전제

| 구분 | 세부 내용 |
| --- | --- |
| **백엔드** | Flask (포트 5000) |
| **프론트엔드** | React (포트 3000) |
| **데이터베이스** | MariaDB 10.x, Redis Sentinel, OpenSearch 2.x |
| **AI · 에이전트** | LangChain + AutoGen, RouteLLM, Ollama (로컬 모델) |
| **런타임** | `/app/miniconda3/envs/bank/bin/python` |
| **컨테이너** | Rootless Podman + Traefik 리버스 프록시 |

## 2. `.env` 템플릿

> 실제 배포 시 **값이 비어 있는 항목을 운영 키로 교체**한 뒤 저장한다.

```dotenv
# ─────────────────────────────
# LLM / Multi-Agent
LLM_PROVIDER=
GOOGLE_API_KEY=
GEMINI_MODEL=
OPENAI_API_KEY=
OPENAI_MODEL=
OLLAMA_BASE_URL=
OLLAMA_API_KEY=
OLLAMA_MODEL=
DEEPINFRA_API_KEY=
DEEPINFRA_MODEL=
DEEPINFRA_BASE_URL=
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=4096
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3

# ─────────────────────────────
# Redis Sentinel
REDIS_SENTINEL_HOSTS=sentinel1:26379,sentinel2:26380,sentinel3:26381
REDIS_SENTINEL_SERVICE_NAME=mymaster
REDIS_PASSWORD=
REDIS_DB=0
REDIS_SOCKET_TIMEOUT=3
REDIS_SOCKET_CONNECT_TIMEOUT=3
REDIS_MAX_CONNECTIONS=50

# ─────────────────────────────
# OpenSearch
OPENSEARCH_HOSTS=https://opensearch:9200
OPENSEARCH_USER=
OPENSEARCH_PASSWORD=
OPENSEARCH_USE_SSL=true
OPENSEARCH_VERIFY_CERTS=true
OPENSEARCH_SSL_ASSERT_HOSTNAME=false
OPENSEARCH_SSL_SHOW_WARN=false
OPENSEARCH_TIMEOUT=30
OPENSEARCH_MAX_RETRIES=3
OPENSEARCH_RETRY_ON_TIMEOUT=true

# ─────────────────────────────
# MariaDB
MARIADB_HOST=mariadb
MARIADB_PORT=3306
MARIADB_USER=
MARIADB_PASSWORD=
MARIADB_DATABASE=reai
MARIADB_CHARSET=utf8mb4
MARIADB_CONNECT_TIMEOUT=5
MARIADB_READ_TIMEOUT=30
MARIADB_WRITE_TIMEOUT=30

DB_INITIALIZED=false

# ─────────────────────────────
# AutoGen Agents
AUTOGEN_ENABLED=true
AUTOGEN_FINANCE_GROUP=finance
AUTOGEN_TRAVEL_GROUP=travel
AUTOGEN_BANKING_GROUP=banking
AUTOGEN_MAX_ROUND=8
AUTOGEN_TIMEOUT=900
AUTOGEN_CODE_EXECUTION=true
AUTOGEN_HUMAN_FEEDBACK=false
AUTOGEN_PARALLEL=true
AUTOGEN_CACHE=true

# ─────────────────────────────
# Langfuse & Phoenix
LANGFUSE_ENABLED=true
LANGFUSE_HOST=
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_DEBUG=false
LANGFUSE_TRACE_LLM=true
LANGFUSE_TRACE_AGENTS=true
LANGFUSE_TRACE_AUTOGEN=true
LANGFUSE_FLUSH_AT=100
LANGFUSE_FLUSH_INTERVAL=5
LANGFUSE_TIMEOUT=10

PHOENIX_ENABLED=true
PHOENIX_ENDPOINT=
PHOENIX_GRPC_ENDPOINT=
PHOENIX_TRACE_LLM=true
PHOENIX_TRACE_EMBEDDINGS=true
PHOENIX_TRACE_RETRIEVALS=true
PHOENIX_COLLECT_METRICS=true
PHOENIX_SAMPLE_RATE=0.1

# ─────────────────────────────
# Search API Keys
GOOGLE_SEARCH_API_KEY=
GOOGLE_SEARCH_ENGINE_ID=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
DAUM_APP_KEY=

# ─────────────────────────────
# Public Data API Keys
BOK_API_KEY=
FSS_API_KEY=
KOREAEXIM_API_KEY=
KFTC_API_KEY=
KFTC_CLIENT_ID=
KFTC_CLIENT_SECRET=
MOLIT_API_KEY=
KOREA_LAND_API_KEY=
KB_REAL_ESTATE_API_KEY=

# ─────────────────────────────
# Cache · Timeout
DB_CONNECTION_POOL_SIZE=20
CACHE_TTL_SECONDS=300
QUERY_TIMEOUT_SECONDS=15

# ─────────────────────────────
# Logging · Testing
DEBUG_MODE=false
LOG_LEVEL=INFO
TESTING_DATABASE_URL=
CACHE_HIT_THRESHOLD=3
CACHE_EVICTION_POLICY=LFU
PRELOAD_CACHE_ENABLED=true
```

## 3. MariaDB 초기 스키마 (`init_schema.sql`)

```sql
-- 스키마 파일 실행 예시:
--   mysql -u$MARIADB_USER -p$MARIADB_PASSWORD reai < init_schema.sql

CREATE TABLE IF NOT EXISTS financial_companies (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    name         VARCHAR(100)    NOT NULL,
    app_id       VARCHAR(100)    NOT NULL UNIQUE,
    category     VARCHAR(50),
    created_at   TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    company_id        BIGINT UNSIGNED NOT NULL,
    content           TEXT            NOT NULL,
    rating            TINYINT UNSIGNED CHECK (rating BETWEEN 1 AND 5),
    review_date       DATETIME,
    platform          ENUM('google_play','app_store') NOT NULL,
    sentiment         ENUM('positive','negative','neutral'),
    sentiment_score   DECIMAL(4,3),
    department_assigned VARCHAR(100),
    processed         BOOLEAN DEFAULT FALSE,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_company (company_id),
    CONSTRAINT fk_company FOREIGN KEY (company_id) REFERENCES financial_companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS departments (
    id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100)  NOT NULL,
    description TEXT,
    keywords    JSON,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CHECK (JSON_VALID(keywords))
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    review_id       BIGINT UNSIGNED NOT NULL,
    agent_type      VARCHAR(50),
    action          VARCHAR(100),
    result          TEXT,
    processing_time FLOAT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_review (review_id),
    CONSTRAINT fk_review FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
);
```

## 4. OpenSearch 인덱스 매핑 스크립트 (`init_opensearch.py`)

```python
#!/app/miniconda3/envs/bank/bin/python
"""OpenSearch 인덱스 & 매핑 생성 스크립트
사용 예:
  python init_opensearch.py --host https://opensearch:9200 --user admin --password ****
"""

import argparse, json, ssl, certifi
from opensearchpy import OpenSearch

INDEX_NAME = "reviews-v1"

MAPPINGS = {
    "settings": {
        "index": {
            "number_of_shards": 3,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "korean": {
                        "type": "custom",
                        "tokenizer": "nori_tokenizer",
                        "filter": ["lowercase", "nori_readingform"]
                    }
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "company_id":        {"type": "long"},
            "content":           {"type": "text", "analyzer": "korean"},
            "rating":            {"type": "byte"},
            "review_date":       {"type": "date"},
            "platform":          {"type": "keyword"},
            "sentiment":         {"type": "keyword"},
            "sentiment_score":   {"type": "float"},
            "department_assigned": {"type": "keyword"},
            "created_at":        {"type": "date"}
        }
    }
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--password", required=True)
    args = p.parse_args()

    client = OpenSearch(
        hosts=[args.host],
        http_auth=(args.user, args.password),
        use_ssl=True,
        verify_certs=True,
        ssl_assert_hostname=False,
        ssl_show_warn=False,
        ca_certs=certifi.where(),
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )

    if client.indices.exists(INDEX_NAME):
        print(f"[SKIP] {INDEX_NAME} 이미 존재")
    else:
        resp = client.indices.create(index=INDEX_NAME, body=MAPPINGS)
        print(json.dumps(resp, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

## 5. 초기화 절차

1. 위 `.env` 파일을 프로젝트 루트에 저장하고 **빈 값을 채운다**.
2. MariaDB 컨테이너 기동 후 `init_schema.sql`을 실행하여 스키마를 생성한다.
3. OpenSearch 컨테이너 기동 & 한국어 형태소 플러그인(Nori) 설치 후 `init_opensearch.py`를 실행한다.
4. 애플리케이션 기동 시 `DB_INITIALIZED=true`로 변경하여 중복 초기화를 방지한다.

---
**작성일**: 2025-07-31
