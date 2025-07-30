#!/usr/bin/env python3
"""
API 테스트 스크립트
"""
import requests
import json
import sys
from datetime import datetime


BASE_URL = "http://localhost:2400/api"


def test_health():
    """헬스 체크 테스트"""
    print("=== 헬스 체크 테스트 ===")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_companies():
    """금융사 API 테스트"""
    print("\n=== 금융사 API 테스트 ===")
    
    # 금융사 목록 조회
    try:
        response = requests.get(f"{BASE_URL}/companies")
        print(f"GET /companies - Status: {response.status_code}")
        companies = response.json()
        print(f"Companies count: {len(companies.get('data', []))}")
        
        if companies.get('data'):
            return companies['data'][0]['id']  # 첫 번째 회사 ID 반환
            
    except Exception as e:
        print(f"Error: {e}")
    
    return None


def test_reviews(company_id):
    """리뷰 API 테스트"""
    print("\n=== 리뷰 API 테스트 ===")
    
    # 리뷰 목록 조회
    try:
        response = requests.get(f"{BASE_URL}/reviews")
        print(f"GET /reviews - Status: {response.status_code}")
        reviews = response.json()
        print(f"Reviews count: {len(reviews.get('data', []))}")
        
        # 특정 회사 리뷰 조회
        if company_id:
            response = requests.get(f"{BASE_URL}/reviews?company_id={company_id}")
            print(f"GET /reviews?company_id={company_id} - Status: {response.status_code}")
            company_reviews = response.json()
            print(f"Company reviews count: {len(company_reviews.get('data', []))}")
        
    except Exception as e:
        print(f"Error: {e}")


def test_sentiment_stats(company_id):
    """감정 통계 API 테스트"""
    print("\n=== 감정 통계 API 테스트 ===")
    
    try:
        # 전체 감정 통계
        response = requests.get(f"{BASE_URL}/reviews/sentiment-stats")
        print(f"GET /reviews/sentiment-stats - Status: {response.status_code}")
        stats = response.json()
        print(f"Total stats: {stats.get('data', {})}")
        
        # 특정 회사 감정 통계
        if company_id:
            response = requests.get(f"{BASE_URL}/reviews/sentiment-stats?company_id={company_id}")
            print(f"GET /reviews/sentiment-stats?company_id={company_id} - Status: {response.status_code}")
            company_stats = response.json()
            print(f"Company stats: {company_stats.get('data', {})}")
        
    except Exception as e:
        print(f"Error: {e}")


def test_departments():
    """부서 API 테스트"""
    print("\n=== 부서 API 테스트 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/departments")
        print(f"GET /departments - Status: {response.status_code}")
        departments = response.json()
        print(f"Departments count: {len(departments.get('data', []))}")
        
        for dept in departments.get('data', [])[:3]:  # 처음 3개만 출력
            print(f"  - {dept['name']}: {dept.get('description', 'N/A')}")
        
    except Exception as e:
        print(f"Error: {e}")


def test_search():
    """검색 API 테스트"""
    print("\n=== 검색 API 테스트 ===")
    
    search_queries = ["앱", "로그인", "고객센터"]
    
    for query in search_queries:
        try:
            response = requests.get(f"{BASE_URL}/reviews/search?q={query}")
            print(f"GET /reviews/search?q={query} - Status: {response.status_code}")
            results = response.json()
            print(f"Search results for '{query}': {len(results.get('data', []))}")
            
        except Exception as e:
            print(f"Error searching for '{query}': {e}")


def main():
    """메인 함수"""
    print("API 테스트 시작...")
    
    # 헬스 체크
    if not test_health():
        print("서버가 실행되지 않았거나 응답하지 않습니다.")
        sys.exit(1)
    
    # 금융사 테스트
    company_id = test_companies()
    
    # 리뷰 테스트
    test_reviews(company_id)
    
    # 감정 통계 테스트
    test_sentiment_stats(company_id)
    
    # 부서 테스트
    test_departments()
    
    # 검색 테스트
    test_search()
    
    print("\n=== API 테스트 완료 ===")


if __name__ == '__main__':
    main()