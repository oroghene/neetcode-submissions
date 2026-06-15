class TrieNode():
    def __init__(self, name: str):
        self.map: Dict[TrieNode] = defaultdict(TrieNode)
        self.name: string = name
        self.value: int = -1

class FileSystem:

    def __init__(self):
        # root node contains the empty string
        self.root = TrieNode("")

    def createPath(self, path: str, value: int) -> bool:
        # obtain all the components
        components = path.split("/")

        # start from the root node
        curr = self.root

        # iterate over all the components
        for i in range(1, len(components)):
            name = components[i]

            # for each component, we check if it exists
            # in the current node's dictionary
            if name not in curr.map:
                # if the components does not exist and
                # the current node is the last one, add it
                if i == len(components) - 1:
                    curr.map[name] = TrieNode(name)
                else:
                    return False
            curr = curr.map[name]

        # value equal to -1 means the path does not exist
        # value not equal to -1 means the path already exists
        # cannot create duplicate path
        if curr.value != -1:
            return False
        
        curr.value = value
        return True

    def get(self, path: str) -> int:
        # obtain all the components
        curr = self.root

        # start from the root
        components = path.split("/")

        # iterate over all the components
        for i in range(1, len(components)):
            # for each component, check if it exists
            # in the current nodes's dictionary
            name = components[i]
            if name not in curr.map:
                return -1
            curr = curr.map[name]
        
        return curr.value


# Your FileSystem object will be instantiated and called as such:
# obj = FileSystem()
# param_1 = obj.createPath(path,value)
# param_2 = obj.get(path)
