class Solution:
    def nextPermutation(self, nums: List[int]) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        # prereqs
        # in-place array manipulation
        # 2 pointers to reverse subarrays
        # lexicographic ordering

        # brute force
        # generate all permutations, sort, find input perm, return next one

        # greedy
        # find next lexicographically greater permutation
        # make smallest possible change that increases array's value
        # find rightmost position to make increase
        # scan right to left
        # find first element smaller than right neighbor
        # this neighbor is called "pivot"
        # find smallest element to right of pivot that is > pivot and swap
        # everything after pivot is in descending order
        # after swap, make everything to right of pivot in ascending order
        # if no pivot (already at largest), reverse entire array (wrap around)

        n = len(nums)
        # find pivot
        pivot = n - 2
        while pivot >= 0 and nums[pivot] >= nums[pivot + 1]:
            pivot -= 1
        
        # find smallest num to right of pivot that is greater than pivot
        if pivot >= 0:
            j = n - 1
            while nums[j] <= nums[pivot]:
                j -= 1
            # swap pivot
            nums[pivot], nums[j] = nums[j], nums[pivot]

        # make everything after pivot ascending
        l, r = pivot + 1, n - 1
        while l <= r:
            nums[l], nums[r] = nums[r], nums[l]
            l, r = l + 1, r - 1