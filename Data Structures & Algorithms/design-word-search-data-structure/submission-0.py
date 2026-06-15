"""
Trie - tree like DS for efficient storage and retrieval
DFS - traverse the trie on wild characters
Recursion = explore all possible character matches for wildcards
"""
class TrieNode:
    def __init__(self) -> TrieNode:
        self.children: Dict[TrieNode] = {}
        self.word: bool = False

class WordDictionary:

    def __init__(self):
        self.root = TrieNode()

    def addWord(self, word: str) -> None:
        curr = self.root
        for c in word:
            if c not in curr.children:
                curr.children[c] = TrieNode()
            curr = curr.children[c]
        curr.word = True

    def search(self, word: str) -> bool:
        def dfs(j: int = 0, root: TrieNode = self.root) -> bool:
            curr = root

            for i in range(j, len(word)):
                c = word[i]
                if c == ".":
                    for child in curr.children.values():
                        if dfs(i + 1, child):
                            return True
                    return False
                else:
                    if c not in curr.children:
                        return False
                    curr = curr.children[c]
            return curr.word
        
        return dfs()
