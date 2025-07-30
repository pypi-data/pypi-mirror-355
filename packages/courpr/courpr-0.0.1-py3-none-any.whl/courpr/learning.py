class Learn():
    """empty."""
    def __init__(self, lang="Python"):
        self.lang = lang

    def learn_process(self):
        print("""Process is started.
The function print() print the text.
example:
    print(\"Hello, world!\"), Try you?""")

ans = input()
if ans == "print(\"Hello, world!\")":
    print("""Yes! Bravo!
The function input() ask and просит, чтобы вы ввели текст,
Try you?""")
ans2 = input()
if ans2 == "input()":
    print("Yes, bravo!")
