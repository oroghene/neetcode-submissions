class Solution:
    def lastStoneWeight(self, stones: List[int]) -> int:
        if not stones or len(stones) == 0:
            return 0
        if len(stones) == 1:
            return stones[0]
        # max heap
        negativestones = [-1 * stone for stone in stones]
        heapq.heapify(negativestones)
        heap = negativestones
        while len(heap) > 1:
            heavieststone = heapq.heappop(heap)
            nextheavieststone = heapq.heappop(heap)
            if heavieststone == nextheavieststone:
                continue
            else:
                heapq.heappush(heap, heavieststone - nextheavieststone)
        return abs(heap[0]) if heap else 0