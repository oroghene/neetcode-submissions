class Solution:
    def calPoints(self, operations: List[str]) -> int:
        points = []
        for op in operations:
            if op == "+":
                p1 = points.pop()
                p2 = points.pop()
                points.append(p2)
                points.append(p1)
                points.append(p1 + p2)
            elif op == "D":
                p1 = points[-1]
                points.append(p1 * 2)
            elif op == "C":
                points.pop()
            else:
                points.append(int(op))
        return sum([int(p) for p in points])