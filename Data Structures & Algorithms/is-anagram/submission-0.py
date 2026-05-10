class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        s_letter_count = [0] * 26
        t_letter_count = [0] * 26
        for c in s:
            s_letter_count[ord(c) - ord('a')] += 1
        for c in t:
            t_letter_count[ord(c) - ord('a')] += 1
        return s_letter_count == t_letter_count