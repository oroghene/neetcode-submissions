"""
graph representation = build adjacency lists from edge
DFS
topological sort - order nodes in DAG so dependencies come first
cycle detetion in graphs
"""
class Solution:
    def findOrder(self, numCourses: int, prerequisites: List[List[int]]) -> List[int]:
        # each course is a node
        # each prereq is an edge
        # add course after all prereqs done
        # build graph where each course points to prereqs
        # cycle track current dfs path
        # visit track fully processed path
        # if in cycle, return empty list
        # dfs all prereq first
        # after all prereq done, add course to result

        # build adjacency list of course to prereqs
        prereq: Dict[int, List[int]] = {c:[] for c in range(numCourses)}
        for crs, pre in prerequisites:
            prereq[crs].append(pre)
        
        output: List[int] = []
        cycle: Set[int] = set()
        visit: Set[int] = set()

        def dfs(crs: int) -> bool:
            if crs in cycle:
                return False
            if crs in visit:
                return True
            
            cycle.add(crs)
            for pre in prereq[crs]:
                if not dfs(pre):
                    return False
            cycle.remove(crs)
            visit.add(crs)
            output.append(crs)
            return True
        
        for c in range(numCourses):
            if dfs(c) == False:
                return []
        return output