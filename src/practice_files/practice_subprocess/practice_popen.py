import subprocess

def main():
    p = subprocess.Popen([
        "python",
        "popen_runner.py",
        ])
    while True:
        return_proc = p.poll()
        if return_proc:
            print(return_proc)
            break


if __name__=="__main__":
    main()

