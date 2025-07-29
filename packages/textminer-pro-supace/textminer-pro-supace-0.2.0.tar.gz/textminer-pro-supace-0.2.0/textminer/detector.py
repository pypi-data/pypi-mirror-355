from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # 항상 같은 결과를 위해 seed 고정

def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "유효한 텍스트를 입력하세요!!"
