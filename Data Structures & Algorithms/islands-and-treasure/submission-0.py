"""
Multi source BFS
"""
class Solution:
    def islandsAndTreasure(self, grid: List[List[int]]) -> None:
        # put all treasure cells in a queue
        # mark them visited 
        # walls are never added
        # set distance = 0
        # while q not empty
        # process all nodes in q
        # for each cell popped, set distance
        # try all neighbors
        # inc dist after level is done

        rows: int = len(grid)
        cols: int = len(grid[0])
        visit: Set[Tuple[int]] = set()
        q: Deque[Tuple[int]]= deque()

        deltas = [[-1, 0], [1, 0], [0, -1], [0, 1]]

        def addCell(r, c):
            if (min(r, c) < 0 or r == rows or c == cols or (r, c) in visit or grid[r][c] == -1):
                return
            visit.add((r, c))
            q.append((r, c))

        # add all gates
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 0:
                    q.append((r,c))
                    visit.add((r,c))
        
        # start bfs
        dist = 0
        while q:
            # process current level
            for i in range(len(q)):
                r, c = q.popleft()
                grid[r][c] = dist
                for dr, dc in deltas:
                    addCell(r + dr, c + dc)
            # inc dist after each level
            dist += 1