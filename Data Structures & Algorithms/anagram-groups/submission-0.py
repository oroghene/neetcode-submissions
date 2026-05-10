class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        
        def getAnagram(s: str):
            s_letter_count = [0] * 26
            for c in s:
                s_letter_count[ord(c) - ord('a')] += 1
            return tuple(s_letter_count)
        
        anagram_to_s = {}
        for s in strs:
            anagram = getAnagram(s)
            if anagram in anagram_to_s:
                anagram_to_s[anagram].append(s)
            else:
                anagram_to_s[anagram] = [s]
        return anagram_to_s.values()