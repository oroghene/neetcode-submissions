# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right

class Solution:
    def getDepth(self, root: Optional[TreeNode]) -> int:
        if not root:
            return 0
        # return 1 + self.getDepth(root.left) + self.getDepth(root.right)
        return 1 + max(self.getDepth(root.left), self.getDepth(root.right))

    def isBalanced(self, root: Optional[TreeNode]) -> bool:
        if not root:
            return True
        
        left_depth = self.getDepth(root.left)
        right_depth = self.getDepth(root.right)
        
        return abs(left_depth - right_depth) < 2 and self.isBalanced(root.left) and self.isBalanced(root.right)