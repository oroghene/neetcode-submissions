# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next

class Solution:
    def reverseList(self, head: Optional[ListNode]) -> Optional[ListNode]:
        # 0 -> 1 -> 2 -> 3
        # 0.next = 1
        # tmp = 0.next
        # tmp = 1
        # cur = 0
        # nxt = null
        # cur.next = nxt
        # cur.next = null
        # cur = tmp
        # null <- 0 1 -> 2 -> 3

        cur = head
        nxt = None
        while cur:
            tmp = cur.next
            cur.next = nxt
            nxt = cur
            cur = tmp
        return nxt
        #                               c
        #                        n
        #                               t
        # none <- 0 <- 1 <- 2 <- 3 | -> none
        # head = 0
        # cur = 0
        # nxt = none
        # tmp = 1