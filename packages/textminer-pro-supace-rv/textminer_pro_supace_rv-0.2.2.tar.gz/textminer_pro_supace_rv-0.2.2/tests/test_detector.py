import pytest
from textminer.detector import detect_language

def test_detect_language_english():
    text = "This is a test sentence written in English."
    assert detect_language(text) == "en"

def test_detect_language_korean():
    text = "안녕하세요 저는 학생입니다."
    assert detect_language(text) == "ko"

def test_detect_language_error():
    assert detect_language("") == "유효한 텍스트를 입력하세요!!"
