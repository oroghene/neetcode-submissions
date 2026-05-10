class Node:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class Queue:
    def __init__(self):
        self.left = None
        self.right = None
        self.size = 0

    def enqueue(self, val: int) -> None:
        node = Node(val)

        # queue is not empty
        if self.right:
            self.right.next = node
            self.right = self.right.next
        # queue is empty
        else:
            self.left = self.right = node
        self.size += 1
        return

    def dequeue(self) -> int | None:
        # queue is not empty
        value = None
        if self.left:
            value = self.left.val
            self.left = self.left.next
            if self.left is None:
                self.right = None
        # queue is empty
        self.size -= 1
        return value

    def empty(self) -> bool:
        return self.size == 0

class MyStack:

    def __init__(self):
        self.stack = Queue()
        self.other = Queue()

    def push(self, x: int) -> None:
        self.stack.enqueue(x)

    def pop(self) -> int:
        while self.stack.size > 1:
            popped = self.stack.dequeue()
            if popped:
                self.other.enqueue(popped)

        value = self.stack.dequeue()

        while self.other.size > 0:
            popped = self.other.dequeue()
            if popped:
                self.stack.enqueue(popped)

        return value            

    def top(self) -> int:
        value = None
        while self.stack.size > 0:
            popped = self.stack.dequeue()
            if popped:
                self.other.enqueue(popped)
                value = popped

        while self.other.size > 0:
            popped = self.other.dequeue()
            if popped:
                self.stack.enqueue(popped)

        return value

    def empty(self) -> bool:
        return self.stack.empty()


# Your MyStack object will be instantiated and called as such:
# obj = MyStack()
# obj.push(x)
# param_2 = obj.pop()
# param_3 = obj.top()
# param_4 = obj.empty()