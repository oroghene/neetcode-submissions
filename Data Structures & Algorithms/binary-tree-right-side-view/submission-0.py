# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right

class Solution:
    def rightSideView(self, root: Optional[TreeNode]) -> List[int]:
        res = []
        if not root:
            return res
        
        curr = root

        level_nodes = [curr]

        while level_nodes:
            level_right_most_val = None
            next_level_nodes = []
            for node in level_nodes:
                level_right_most_val = node.val
                if node.left:
                    next_level_nodes.append(node.left)
                if node.right:
                    next_level_nodes.append(node.right)
            level_nodes = next_level_nodes
            res.append(level_right_most_val)
        return res