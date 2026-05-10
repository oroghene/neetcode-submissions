class Solution:
    def removeElement(self, nums: List[int], val: int) -> int:
        tmp = []
        res = 0
        for n in nums:
            if n != val:
                tmp.append(n)
                res += 1
        for i in range(len(tmp)):
            nums[i] = tmp[i]
        return res