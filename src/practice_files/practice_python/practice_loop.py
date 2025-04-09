"""
Loop가 중첩되어있을 때 for-else 구문의 else 섹션에서 break하더라도 바깥 loop까지 빠져나가지 않는다.
"""
def loop_stopper(n):
    while True:
        for i in range(10):
            if i == n:
                print("Breakpoint")
                break
        else:
            print("StopIteration")
            break
        print("In while loop")
        break

    print("Outside while loop")

print("Stop in for-loop")
loop_stopper(5)

print("Stop after for-loop")
loop_stopper(100)

