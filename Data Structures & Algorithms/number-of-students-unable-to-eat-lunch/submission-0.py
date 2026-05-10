class Node:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

class Queue:
    def __init__(self):
        self.head = Node()

    def enqueue(self, val):
        return
    
    def dequeue(self):

        return

class Solution:
    def countStudents(self, students: List[int], sandwiches: List[int]) -> int:
        # students   = [1,1,1,0,0,1]
        # sandwiches = [1,0,0,0,1,1]

        # students   = [1,1,0,0,1]
        # sandwiches = [0,0,0,1,1]

        # students   = [1,0,0,1,1]
        # sandwiches = [0,0,0,1,1]

        # students   = [0,0,1,1,1]
        # sandwiches = [0,0,0,1,1]

        # students   = [0,1,1,1]
        # sandwiches = [0,0,1,1]

        # students   = [1,1,1]
        # sandwiches = [0,1,1]
        hungry_students = len(students)
        while True:
            if hungry_students == 0 and len(sandwiches) == 0:
                return 0
            elif sandwiches[0] == students[0]:
                sandwiches.pop(0)
                students.pop(0)
                hungry_students -= 1
            else:
                picky_students = 0
                while True:
                    students.append(students.pop(0))
                    if sandwiches[0] == students[0]:
                        break
                    picky_students += 1
                    if picky_students == hungry_students:
                        return hungry_students
        return hungry_students