"""
prereqs
tree data structures - understand parent child relationships and tree traversal
hash maps / arrays for children - store and access child nodes efficiently
string processing - char by char iteration and ASCII manipulation
oop - create classes with methods that maintain internal state

a prefix tree is a tree like ds for fas string ops
each node is a char and paths from root are words
common prefixes are shared. saves space
each node has 26 children for letters a-z
boolean flag says a word is completed at that node

"""
class TrieNode:
    def __init__(self) -> TrieNode:
        self.children: List[str] = [None] * 26
        self.endOfWord: bool = False

class PrefixTree:

    def __init__(self):
        self.root = TrieNode()        

    def insert(self, word: str) -> None:
        curr = self.root
        for c in word:
            i = ord(c) - ord('a')
            if curr.children[i] == None:
                curr.children[i] = TrieNode()
            curr = curr.children[i]
        curr.endOfWord = True

    def search(self, word: str) -> bool:
        curr = self.root
        for c in word:
            i = ord(c) - ord('a')
            if curr.children[i] == None:
                return False
            curr = curr.children[i]
        return curr.endOfWord

    def startsWith(self, prefix: str) -> bool:
        curr = self.root
        for c in prefix:
            i = ord(c) - ord('a')
            if curr.children[i] == None:
                return False
            curr = curr.children[i]
        return True
        