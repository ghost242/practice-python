import difflib
from konlpy.tag import Kkma


# text1 = '''  1. Beautiful is better than ugly.
#   2. Explicit is better than implicit.
#   3. Simple is better than complex.
#   4. Complex is better than complicated.
# '''.splitlines(keepends=True)
# len(text1)

# text1[0][-1]

# text2 = '''  1. Beautiful is better than ugly.
#   3.   Simple is better than complex.
#   4. Complicated is better than complex.
#   5. Flat is better than nested.
# '''.splitlines(keepends=True)

# d = difflib.Differ()

# print(*list(d.compare(
#     text1,
#     text2
# )), sep='\n')

# base, comp = text1[0], text2[0]

from polyglot.text import Text

base = "[바이오USA] SK바이오팜, 피닉스랩과 생성형 AI 개발 MOU - 조선비즈"
comp = "SK바이오팜, 피닉스랩과 AI 기반 신약 개발 MOU 체결"


t1 = Text(base)
t2 = Text(comp)

print(t1.words)
print(t2.words)


def similarity(w1, w2):
    sw1 = set(w1)
    sw2 = set(w2)
    iw = sw1 & sw2
    uw = sw1 | sw2

    print(iw)
    print(uw)

    return len(sw1 & sw2) / len(sw1 | sw2)


print(similarity(t1.words, t2.words))
