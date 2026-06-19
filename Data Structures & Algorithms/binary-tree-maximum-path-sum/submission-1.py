# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right

class Solution:
    def maxPathSum(self, root: Optional[TreeNode]) -> int:
        res = [root.val]
        def dfs(root = root):
            # base case
            if not root:
                return 0
            # recursive case for left subtree
            leftmax = dfs(root.left)
            leftmax = max(leftmax, 0)
            # recursive case for right subtree
            rightmax = dfs(root.right)
            rightmax = max(rightmax, 0)

            # max with left subtree and right subtree
            res[0] = max(res[0], root.val + leftmax + rightmax)
            # max with left subtree or right subtree
            return root.val + max(leftmax, rightmax)
        
        dfs()
        return res[0]