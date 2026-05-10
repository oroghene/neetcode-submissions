class Solution:
    def combinationSum(self, nums: List[int], target: int) -> List[List[int]]:
        res = []
        def dfs(index: int, combosum: int, combo: List[int]) -> List[int]:
            if combosum == target:
                res.append(combo[::])
                return
            if index >= len(nums) or combosum > target:
                return

            combo.append(nums[index])
            dfs(index, combosum + nums[index], combo)
            combo.pop()
            dfs(index + 1, combosum, combo)

        dfs(0, 0, [])
        return res
