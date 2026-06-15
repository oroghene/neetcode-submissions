class Solution:
    def permute(self, nums: List[int]) -> List[List[int]]:
        # backtracking is the only way for normal person to solve this
        # 2 choices in backtracking, choose this and continue to next
        # or skip this and continue to next (choose from unchosen numbers)
        # backtracking builds permutations by choosing numbers one by one 
        # and exploring all possible orders
        # at every step
        # good and only base case
        # at a full permutation, (check length), add to result
        # first choice
        # pick this number that has not been used yet
        # add it to the current permutation
        # recursively continue building
        # second choice
        # backtrack (remove this number) and pick next number

        res = []
        n = len(nums)
        picked = [False] * n
        def backtrack(perm: List[int], picked: List[bool]) -> None:
            # good and only base case
            if len(perm) == len(nums):
                res.append(perm[::])
                return
            for i in range(len(nums)):
                # first choice
                if not picked[i]:
                    perm.append(nums[i])
                    picked[i] = True
                    # second choice
                    backtrack(perm, picked)
                    perm.pop()
                    picked[i] = False

        backtrack([], picked)
        return res