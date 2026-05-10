class Solution:
    def getSCharCount(self, s: str, charcount: List[int]) -> None:
        for sc in s:
            index = ord(sc) - ord('a')
            charcount[index] += 1

    def isAnagram(self, s: str, t: str) -> bool:
        scharcount = [0] * 26
        tcharcount = [0] * 26
        self.getSCharCount(s, scharcount)
        self.getSCharCount(t, tcharcount)
        return scharcount == tcharcount
