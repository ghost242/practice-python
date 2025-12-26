from konlpy.tag import Okt, Kkma

# Initialize Korean text processors
okt = Okt()
kkma = Kkma()

# Example text processing
text = "염료, 조제 무기안료, 유연제 및 기타 착색제 제조업"
print(okt.morphs(text))  # Morphological analysis
print(okt.pos(text))  # Part-of-speech tagging
