# 좀처럼 우회할 수 없는 것으로 보아 통상적인 방법으로는 불가능하다고 봐야 할 것으로 보임.

from practice_circular_import import func_b, func_c, func_a

if __name__ == "__main__":
    func_a()
    func_b()
    func_c()
