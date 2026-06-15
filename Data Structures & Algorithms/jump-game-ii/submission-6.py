class Solution:
    def jump(self, nums: List[int]) -> int:
        # min number of jumps to reach last index
        # is level by level similar to bfs
        # each level is all possible end positions for that jump
        # for each position, see how far next jump will land
        # instead of q, use greedy window
        # [l, r] represents range of indices reachable
        # find farthest we can reach in next jump

        res = 0
        l = r = 0
        while r < len(nums) - 1:
            farthest = 0
            for i in range(l, r + 1):
                farthest = max(farthest, i + nums[i])
            l = r + 1
            r = farthest
            res += 1
        return res