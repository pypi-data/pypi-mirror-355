from langdetect import detect

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except:
        return "언어를 감지할 수 없습니다"
