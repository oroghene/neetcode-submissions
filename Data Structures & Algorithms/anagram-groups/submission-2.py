class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        def getanagram(s):
            dna = [0] * 26
            for c in s:
                dna[ord(c) - ord('a')] += 1
            return tuple(dna)
        
        counter = {}
        for s in strs:
            s_ana = getanagram(s)
            if s_ana in counter:
                counter[s_ana].append(s)
            else:
                counter[s_ana] = [s]
        return list(counter.values())