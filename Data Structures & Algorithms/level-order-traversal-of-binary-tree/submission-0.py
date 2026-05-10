# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right

class Solution:
    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        res = []
        if not root:
            return res
        
        curr = root
        level_nodes = [curr]
        level_vals = [curr.val]
        while level_nodes:
            next_level_nodes = []
            curr_level_vals = []
            for node in level_nodes:
                curr_level_vals.append(node.val)
                if node.left:
                    next_level_nodes.append(node.left)
                if node.right:
                    next_level_nodes.append(node.right)
            level_nodes = next_level_nodes
            res.append(curr_level_vals)
        return res