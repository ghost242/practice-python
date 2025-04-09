from operator import add, sub, mul, truediv

funcs = [add, sub, mul, truediv]
op = int(input("연산자 선택(1: +, 2: -, 3: *, 4: /):"))
a, b = map(int, input("계산할 두 숫자를 입력:").split())

print(funcs[op - 1](a, b))
