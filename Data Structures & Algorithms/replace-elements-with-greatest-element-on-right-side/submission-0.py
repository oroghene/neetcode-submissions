class Solution:
    def replaceElements(self, arr: List[int]) -> List[int]:
        maxx = -1
        for i in range(len(arr) - 1, -1, -1):
            tmpmaxx = max(maxx, arr[i])
            arr[i] = maxx
            maxx = tmpmaxx
        return arr