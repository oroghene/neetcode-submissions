# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:    
    def mergeKLists(self, lists: List[Optional[ListNode]]) -> Optional[ListNode]:
        # merge 2 lists
        # base case merge 2 lists
        # recursive case call merge k lists with left half
        # recursive case call merge k lists with right half
        # recursive case call merge these 2 halfs
        if not lists or len(lists) == 0:
            return None
        
        while len(lists) > 1:
            mergedLists = []
            for i in range(0, len(lists), 2):
                l1 = lists[i]
                l2 = lists[i + 1] if (i + 1) < len(lists) else None
                mergedLists.append(self.merge2Lists(l1, l2))
            lists = mergedLists

        return lists[0]

    def merge2Lists(self, list1: Optional[ListNode], list2: Optional[ListNode]) -> Optional[ListNode]:
        l1 = list1
        l2 = list2
        l3 = ListNode()
        node = l3
        while l1 and l2:
            v1 = l1.val if l1 else None
            v2 = l2.val if l2 else None
            if v1 < v2:
                node.next = l1
                l1 = l1.next
            else:
                node.next = l2
                l2 = l2.next
            node = node.next
        if l1:
            node.next = l1
        if l2:
            node.next = l2
        return l3.next