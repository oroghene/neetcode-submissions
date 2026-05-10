class Solution:
    def kClosest(self, points: List[List[int]], k: int) -> List[List[int]]:
        distances = []
        for x, y in points:
            x2 = x*x
            y2 = y*y
            d = x2 + y2
            distances.append(tuple([d, x, y]))
        heapq.heapify(distances)
        heap = distances
        res = []
        for _ in range(k):
            d, x, y = heapq.heappop(heap)
            res.append([x,y])
        return res