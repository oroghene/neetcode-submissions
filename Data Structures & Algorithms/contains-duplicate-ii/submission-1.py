class Solution:
    def containsNearbyDuplicate(self, nums: List[int], k: int) -> bool:
        if k == 0:
            return False
        seen = set()
        l = 0
        for r in range(len(nums)):
            if nums[r] in seen and abs(r - l) <= k:
                return True
            if r - l + 1 > k:
                seen.remove(nums[l])
                l += 1
            seen.add(nums[r])
        return False