import sys
sys.path.append('/content/textminer_pro')
from textminer import detect_language

text1 = "This is an English sentence."
text2 = "이 문장은 한국어입니다."

print("English 감지 결과:", detect_language(text1))
print("Korean 감지 결과:", detect_language(text2))
