class Solution:
    def longestOnes(self, nums: List[int], k: int) -> int:
        # sliding window
        l = res = 0
        for r in range(len(nums)):
            k -= (1 - nums[r])
            while k < 0:
                if nums[l] == 0:
                    k += 1
                l += 1
            res = max(res, r - l + 1)
        return res