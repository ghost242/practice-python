from kiwipiepy import Kiwi

s = "염료, 조제 무기안료, 유연제 및 기타 착색제 제조업"
base = "[바이오USA] SK바이오팜, 피닉스랩과 생성형 AI 개발 MOU - 조선비즈"

processor = Kiwi()

print([(token.form, token.tag) for token in processor.tokenize(base)])
