class Solution:
    def numOfSubarrays(self, arr: List[int], k: int, threshold: int) -> int:
        res = 0
        l = 0
        cursum = 0
        
        for r in range(len(arr)):
            if r - l + 1 > k:
                cursum -= arr[l]
                l += 1
            cursum += arr[r]
            avg = cursum / k
            if r - l + 1 == k and avg >= threshold:
                res += 1
        return res