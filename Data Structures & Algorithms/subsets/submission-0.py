class Solution:
    def subsets(self, nums: List[int]) -> List[List[int]]:
        res = [[]]
        for num in nums:
            res_copy = res[::]
            for level in res_copy:
                new_level = level  + [num]
                res.append(new_level)
        return res
    """
    res [[], [1]]
    res_copy [[], [1]]
    1                               []
                           /                \
    2                  [1]                    []
                    /         \             /   \
    3            [1,2]         [1]       [2]     []
                /    \       /    \    /    \   /  \
             [1,2,3] [1,2] [1,3] [1] [2,3] [2] [3] []
    """