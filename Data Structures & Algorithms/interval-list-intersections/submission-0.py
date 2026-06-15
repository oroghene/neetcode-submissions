class Solution:
    def intervalIntersection(self, firstList: List[List[int]], secondList: List[List[int]]) -> List[List[int]]:
        # intervals
        # 2 pointers
        # line sweep
        # sorted arrays

        def bruteforce(listA: List[List[int]], listB: List[List[int]]) -> List[List[int]]:
            # check every interval from list 2 with each interval from list 1
            # intersection if 1 interval starts before another ends
            # redundany
            res = []
            for a, b in listA:
                for c, d in listB:
                    if a <= c <= b or c <= a <= d:
                        res.append([max(a, c), min(b, d)])
            return res
        
        return bruteforce(firstList, secondList)