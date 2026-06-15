class Solution:
    def combinationSum(self, nums: List[int], target: int) -> List[List[int]]:
        res = []
        def dfs(index: int, combosum: int, combo: List[int]) -> List[int]:
            # good base case, found combo that sums to target
            if combosum == target:
                res.append(combo[::])
                return
            # bad base case, combo sum not good, or out of bounds
            if index >= len(nums) or combosum > target:
                return

            # choice 1 to add this and continue here
            # add this
            combo.append(nums[index])
            # continue here
            dfs(index, combosum + nums[index], combo)

            # choice 2 to backtrack and continue elsewhere
            # backtrack
            combo.pop()
            # continue elsewhere
            dfs(index + 1, combosum, combo)

        dfs(0, 0, [])
        return res
