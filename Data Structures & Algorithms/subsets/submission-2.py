class Solution:
    def subsets(self, nums: List[int]) -> List[List[int]]:
        # recursion (explore decision trees)
        # backtracking (undo choices, remove elements after exploring)
        res = []
        subset = []

        def backtrack(i: int = 0) -> None:
            # build all possible subsets by making a choice at each step
            # for each number, 2 optiont = include it or exclude it
            # this forms decision tree
            # at end of array, current array is a subset
            # maintain result and subset arrays
            # for i in range len, if i at end, add subset copy to res
            # else 2 options
            # add i to subset and pop and continue
            # or just continue without i
            
            if i >= len(nums):
                res.append(subset[::])
                return
            # add
            subset.append(nums[i])
            backtrack(i + 1)
            # backtrack
            subset.pop()
            # just continue
            backtrack(i + 1)
            return

        backtrack()
        return res