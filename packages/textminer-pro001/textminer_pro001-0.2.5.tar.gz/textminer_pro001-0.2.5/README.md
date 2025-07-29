# textminer-pro

자연어 텍스트 처리의 기본 기능을 제공하는 Python 패키지입니다.
## 불용어 처리
text = """
The stage is set for a grand parade to celebrate the U.S. Army's 250th anniversary, which falls on the same day as President Donald Trump's 79th birthday and Flag Day.
The day-long festival will take place primarily at the National Mall in Washington, D.C. on Saturday, June 14, with music performances, fireworks and a pomp-filled procession through the streets.
More than two dozen M1 Abrams tanks, scores of infantry vehicles and thousands of soldiers are expected to be involved in the event. Trump, himself, will be watching the parade from a reviewing stand just south of the White House that is now being constructed for the occasion.
"""


cleaned = remove_stopwords(text)
print("불용어 제거 결과:")
print(cleaned)


## 키워드 추출
keywords = extract_keywords(text, top_n=5)

## 텍스트 요약
summary = summarize_text(text, num_sentences=2)
---



