class Solution:
    def intervalIntersection(self, firstList: List[List[int]], secondList: List[List[int]]) -> List[List[int]]:
        # intervals
        # 2 pointers
        # line sweep
        # sorted arrays

        def bruteforce(listA: List[List[int]], listB: List[List[int]]) -> List[List[int]]:
            """time: O(m*n), space: O(m+n)"""
            # check every interval from list 2 with each interval from list 1
            # intersection if 1 interval starts before another ends
            # redundany
            res = []
            for a, b in listA:
                for c, d in listB:
                    if a <= c <= b or c <= a <= d:
                        res.append([max(a, c), min(b, d)])
            return res
        
        # return bruteforce(firstList, secondList)

        # line sweep
        # treats intervals as events on number line
        # at each interval start, incremenet active counter
        # at each interval end, decremenet active counter
        # if active counter = 2, it means intersection
        # bc interval from list a and interval from list b are
        # covering the same point at the same time
        # process all intervals in sorted order
        # algo
        # create map to store events
        # for each interval, +1 at start, -1 at end
        # sort all events
        # before updating counter, if active == 2
        # record intersection from prev position
        # to current position -1 

        def linesweep(listA: List[List[int]], listB: List[List[int]]) -> List[List[int]]:
            """time: O((m+n)log(m+n)), space: O(m+n)"""
            mp = defaultdict(int)
            for s, e in listA:
                mp[s] += 1
                mp[e + 1] -= 1
            for s, e in listA:
                mp[s] += 1
                mp[e + 1] -= 1
            
            res = []
            active = 0
            prev = None
            for x in sorted(mp):
                if active == 2:
                    res.append([prev, x - 1])
                active += mp[x]
                prev = x
            return res

        def twoPointers(listA: List[List[int]], listB: List[List[int]]) -> List[List[int]]:
            """time: O(m+n), space: O(m + n)"""
            # both lists are sorted and disjoint (no common elements)
            # at each step, compare current interval from each list
            # record intersection if overlap
            # advance pointer for which interval ends first
            # because it cannot intersect with future interval from other list
            res = []
            i = j = 0

            while i < len(listA) and j < len(listB):
                sa, ea = listA[i]
                sb, eb = listB[j]

                start = max(sa, sb)
                end = min(ea, eb)

                if start <= end:
                    res.append([start, end])
                
                if ea < eb:
                    i += 1
                else:
                    j += 1
            return res

        return twoPointers(firstList, secondList)