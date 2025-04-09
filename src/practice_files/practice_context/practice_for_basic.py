from contextvars import ContextVar, copy_context
import threading


def th_1_func():
    v1 = ContextVar("VarName1")
    v1.set("hello")

    ctx = copy_context()
    print([(k, v) for k, v in ctx.items()])


def th_2_func():
    v2 = ContextVar("Thread2Var")
    v2.set(1002312)

    ctx = copy_context()
    print([(k, v) for k, v in ctx.items()])


def main():
    th_1 = threading.Thread(target=th_1_func)
    th_2 = threading.Thread(target=th_2_func)

    th_1.start()
    th_2.start()

    th_1.join()
    th_2.join()


if __name__ == "__main__":
    main()
    # # context variable을 만드는 코드
    # var = ContextVar('var_name')
    # # 기본값을 포함하는 context variable을 만드는 코드
    # var_default = ContextVar('default_var', default=100)
    #
    # token = var.set('new value')
    #
    # # 현재 시점의 context variable을 반환하는 코드
    # # ctx_1 = ('var_name': 'new_value')
    # ctx_1 = copy_context()
    # print([(k, v) for k, v in ctx_1.items()])
    #
    # # 'var_name' 키를 갖는 context variable 값을 제거하는 코드
    # var.reset(token)
    #
    # # 현재 시점의 context variable을 반환하는 코드
    # # ctx_2 = ()
    # ctx_2 = copy_context()
    # print([(k, v) for k, v in ctx_2.items()])
    #
    # token2 = var_default.set(500)
    #
    # # 현재 시점의 context variable을 반환하는 코드
    # # var_default = 500
    # # ctx_3 = ('default_var': 500)
    # print(var_default.get())
    # ctx_3 = copy_context()
    # print([(k, v) for k, v in ctx_3.items()])
    #
    # var_default.reset(token2)
    #
    # # 현재 시점의 context variable을 반환하는 코드
    # # var_default = 500
    # # ctx_4 = ()
    # print(var_default.get())
    # ctx_4 = copy_context()
    # print([(k, v) for k, v in ctx_4.items()])
    #
    # # def main():
    # #     # 'var' was set to 'spam' before
    # #     # calling 'copy_context()' and 'ctx.run(main)', so:
    # #     print(var.get())
    # #     print(var.get() == ctx[var] == 'spam')
    # #
    # #     var.set('ham')
    # #
    # #     # Now, after setting 'var' to 'ham':
    # #     print(var.get())
    # #     print(var.get() == ctx[var] == 'ham')
    # #
    # # ctx = copy_context()
    # #
    # # # Any changes that the 'main' function makes to 'var'
    # # # will be contained in 'ctx'.
    # # ctx.run(main)
    # #
    # # # The 'main()' function was run in the 'ctx' context,
    # # # so changes to 'var' are contained in it:
    # # print(var.get())
    # # print(ctx[var] == 'ham')
    # #
    # # # However, outside of 'ctx', 'var' is still set to 'spam':
    # # print(var.get())
    # # print(var.get() == 'spam')
