# Definition for a binary tree node.
# class TreeNode:
#     def __init__(self, val=0, left=None, right=None):
#         self.val = val
#         self.left = left
#         self.right = right

class Solution:
    def getIndex(self, traversal: List[int], val: int) -> int:
        for i in range(len(traversal)):
            if traversal[i] == val:
                return i

    def buildTree(self, preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
        if not preorder or len(preorder) == 0:
            return None
        if len(preorder) == 1:
            return TreeNode(preorder[0])
        root = TreeNode(preorder[0])

        inorder_root_index = self.getIndex(inorder, root.val)

        root_left_child_inorder_traversal = inorder[:inorder_root_index]
        root_right_child_inorder_traversal = inorder[inorder_root_index + 1:]
        
        root_left_child_preorder_traversal = preorder[1: inorder_root_index + 1]
        root_right_child_preorder_traversal = preorder[inorder_root_index + 1:]

        root.left = self.buildTree(root_left_child_preorder_traversal, root_left_child_inorder_traversal)
        root.right = self.buildTree(root_right_child_preorder_traversal, root_right_child_inorder_traversal)

        return root