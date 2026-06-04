class Solution:
    def setZeroes(self, matrix: List[List[int]]) -> None:
        """
        Do not return anything, modify matrix in-place instead.
        """
        zeros = []
        rows = len(matrix)
        cols = len(matrix[0])

        for r in range(rows):
            for c in range(cols):
                if matrix[r][c] == 0:
                    zeros.append((r,c))

        for zr, zc in zeros:
            for c in range(cols):
                matrix[zr][c] = 0
            for r in range(rows):
                matrix[r][zc] = 0