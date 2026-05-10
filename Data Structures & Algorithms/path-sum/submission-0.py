# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right
class Solution:
    def hasPathSum(self, root: Optional[TreeNode], targetSum: int) -> bool:
        if not root:
            return False
        
        if not root.left and not root.right:
            return root.val == targetSum

        new_target_sum = targetSum - root.val
        return self.hasPathSum(root.left, new_target_sum) or self.hasPathSum(root.right, new_target_sum)
        """
               1(2)
             /      \
           1(1)      0(1)
          /  \      /   \
         1(0) N(0) N(1) N(1)
        /
      N(-1)
        """