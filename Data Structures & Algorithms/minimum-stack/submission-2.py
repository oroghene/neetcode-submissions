class MinStack:

    def __init__(self):
        self.stack = []
        self.minstack = []
        self.size = 0
        self.min = 0

    def push(self, val: int) -> None:
        if self.size == 0:
            self.min = val
        else:
            self.min = min(self.min, val)

        self.minstack.append(self.min)
        self.stack.append(val)
        self.size += 1

    def pop(self) -> None:
        self.stack.pop()
        self.minstack.pop()
        self.size -= 1
        if self.size > 0:
            self.min = self.minstack[-1]

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.minstack[-1]