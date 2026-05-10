class Solution:
    def getConcatenation(self, nums: List[int]) -> List[int]:
        n = len(nums)
        ans = [0 for _ in range(2*n)]
        i = 0
        while i < (2*n):
            j = 0
            while j < n:
                ans[i] = nums[j]
                j += 1
                i += 1
        return ans