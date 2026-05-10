# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right

class Solution:
    def inOrderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        if not root:
            return []
        return self.inOrderTraversal(root.left) + [root.val] + self.inOrderTraversal(root.right)

    def kthSmallest(self, root: Optional[TreeNode], k: int) -> int:
        return self.inOrderTraversal(root)[k-1]