class Solution:
    def findKthLargest(self, nums: List[int], k: int) -> int:
        n = len(nums)
        neganums = [-num for num in nums]
        heapq.heapify(neganums)
        for _ in range(k - 1):
            heapq.heappop(neganums)
        return -neganums[0]