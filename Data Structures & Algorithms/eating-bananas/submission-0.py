class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:

        def eatingHours(speed):
            total_hours = 0
            for p in piles:
                hours = p // speed
                minutes = p % speed
                if minutes > 0:
                    hours += 1
                total_hours += hours
            return total_hours

        l, r = 1, max(piles)
        res = r
        while l <= r:
            k = (l + r) // 2
            hours = eatingHours(k)
            if hours <= h:
                res = k
                r = k - 1
            else:
                l = k + 1
        return res