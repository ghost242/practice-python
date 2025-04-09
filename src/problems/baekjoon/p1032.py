from itertools import zip_longest

n = int(input())

comp = ""
for _ in range(n):
    s = input()

    if not comp:
        comp = s
    else:
        _comp = ""
        for a, b in zip_longest(comp, s, fillvalue="?"):
            if a == b:
                _comp += a
            else:
                _comp += "?"
        comp = _comp
 
print(comp)
