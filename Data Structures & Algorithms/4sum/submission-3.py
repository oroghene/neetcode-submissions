class Solution:
    def fourSum(self, nums: List[int], target: int) -> List[List[int]]:
        # sort before using ksum and 2 pointers
        nums.sort()
        quad = []
        res = []

        def kSum(k, start, target):
            # base case (k == 2)
            if k == 2:
                # use 2 pointers
                l, r = start, len(nums) - 1
                while l < r:
                    if nums[l] + nums[r] < target:
                        l += 1
                    elif nums[l] + nums[r] > target:
                        r -= 1
                    elif nums[l] + nums[r] == target:
                        res.append(quad + [nums[l], nums[r]])
                        l += 1
                        r -= 1
                        # skip duplicates
                        while l < r and nums[l] == nums[l - 1]:
                            l += 1
                        while l < r and nums[r] == nums[r + 1]:
                            r -= 1
                return
            # recursive case (k > 2)
            # for loop
            for i in range(start, len(nums) - k + 1):
                if i > start and nums[i] == nums[i - 1]:
                    continue
                quad.append(nums[i])
                kSum(k - 1, i + 1, target - nums[i])
                # backtrack
                quad.pop()
        
        # call k sum helper
        kSum(4, 0, target)
        return res