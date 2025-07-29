# textminer-pro

자연어 텍스트 처리의 기본 기능을 제공하는 Python 패키지입니다.
## 키워드 추출
from textminer import extract_keywords

text = "Apple is looking at buying a U.K. startup for $1 billion."
keywords = extract_keywords(text, top_n=3)
print(keywords)
['spider-man', 'character', 'movie']

## 언어 감지
from textminer import detect_language

print(detect_language("This is an English sentence."))  # 'en'
print(detect_language("안녕하세요 반갑습니다."))            # 'ko'
print(detect_language(""))                              # '유효한 텍스트를 입력하세요.'

## 텍스트 요약
from textminer import summarize_text

text = '''
Our hub and spoke model sees us headquartered in Utrecht, the Netherlands with specialised operations in key global regions. This allows us to centralise our key functions and strategies while building networks and managing sector and landscape programs where the action is happening.
'''

summary = summarize_text(text, num_sentences=2)
print(summary)
---

## 🔧 설치 방법

```bash
git clone https://github.com/Hansupace/textminer-pro.git
cd textminer-pro
pip install -r requirements.txt

