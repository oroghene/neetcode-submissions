class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        # search start and end
        up = 0
        down = len(matrix) - 1
        left = 0
        right = len(matrix[0]) - 1
        row = -1

        while up <= down:
            row = (up + down) // 2
            # find the row that contains the target
            # go down if end of row < target
            if matrix[row][-1] < target:
                up = row + 1
            # go up if start of row > target
            elif matrix[row][0] > target:
                down = row - 1
            else:
                break

        # in the row that contains the target
        while left <= right:
            m = (left + right) // 2
            if matrix[row][m] == target:
                return True
            elif matrix[row][m] < target:
                left = m + 1
            else:
                right = m - 1
        return False