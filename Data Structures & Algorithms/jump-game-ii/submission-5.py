class Solution:
    def jump(self, nums: List[int]) -> int:
        # prereqs
        # dynamic programming memoization cache recursive subproblem to avoid recomputation
        # dynamic programming tabulation build solutions bottom up using iterative DP
        # greedy algo - make locally optimized solution that leads to global optimal solution
        # bfs level by level traversal to find minimum # of step

        def dfs(i: int = 0) -> int:
            """time: O(n!) TLE, space: O(n)"""
            # good base case
            if i == len(nums) - 1:
                return 0
            # bad base case
            if nums[i] == 0:
                return float('inf')

            # recursive case
            end = min(len(nums) - 1, i + nums[i])
            res = float('inf')
            for j in range(i + 1, 1 + end):
                res = min(res, 1 + dfs(j))
            return res

        # return dfs()

        dp = {}
        def cached_dfs(i: int = 0) -> int:
            """time: O(n^2) TLE, space: O(n)"""
            # memoization to prevent repeat work
            if i in dp:
                return dp[i]
            # good base case
            if i == len(nums) - 1:
                return 0
            # bad base case
            if nums[i] == 0:
                return float('inf')

            # recursive case
            res = float('inf')
            end = min(len(nums) - 1, i + nums[i])
            for j in range(i + 1, 1 + end):
                res = min(res, 1 + dfs(j))
            dp[i] = res
            return res

        # return cached_dfs()


        def bottom_up_tabularization_dp(nums: List[int]) -> int:
            """time: O(n^2) TLE, space: O(n)"""
            # fill dp array right to left
            n = len(nums)
            dp = [float('inf')] * n
            dp[n - 1] = 0
            
            for i in range(n - 2, -1, -1):
                end = min(n, i + nums[i] + 1)
                for j in range(i + 1, end):
                    dp[i] = min(dp[i], 1 + dp[j])
            
            return dp[0]

        return bottom_up_tabularization_dp(nums)