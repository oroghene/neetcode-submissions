class Solution:
    def maxSubArray(self, nums: List[int]) -> int:
        res = nums[0]
        cur = 0
        for n in nums:
            cur = max(cur, 0)
            cur += n
            res = max(res, cur)
        return res