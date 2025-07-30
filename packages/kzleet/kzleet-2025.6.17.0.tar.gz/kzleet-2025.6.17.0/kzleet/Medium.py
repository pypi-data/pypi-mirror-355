from .Solution import Solution

class Solution_386_A(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 386, 'Medium')

    main = None

    def lexicalOrder(self, n):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/lexicographical-numbers/?envType=daily-question&envId=2025-06-08

        :type n: int
        :rtype: List[int]
        '''

        result = []

        def s(x):
            if x > n:
                return

            result.append(x)

            for i in range(10):
                a = x * 10 + i # include 0 for 10 --> 100 up to 109
                if a > n: return # efficiency
                s(a)

        for i in range(1, 10):
            s(i)

        return result

    main = lexicalOrder

class Solution_386_B(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 386, 'Medium')

    main = None

    def lexicalOrder(self, n):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/lexicographical-numbers/?envType=daily-question&envId=2025-06-08

        :type n: int
        :rtype: List[int]
        '''

        result = []

        def s(x):
            result.append(x)

            if x * 10 <= n: s(x * 10)

            if x % 10 != 9 and x < n: s(x + 1)

        s(1)

        return result

    main = lexicalOrder

class Solution_909(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 909, 'Medium')

    def snakesAndLadders(self, board):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/snakes-and-ladders/description/?envType=daily-question&envId=2025-05-31

        :type board: List[List[int]]
        :rtype: int
        '''

        flat = []
        n = len(board)
        for i in range(n - 1, -1, -1): # provided in reverse
            row = board[i]
            if (n - 1 - i) % 2 == 0:
                flat.extend(row)
            else:
                flat.extend(reversed(row))

        queue = [(0, 0)]  # (position, rolls)
        visited = set([0])
        front = 0

        n = len(flat)
        while front < len(queue):
            pos, rolls = queue[front]
            front += 1

            if pos == n - 1:
                return rolls

            for k in range(1, 7):
                next_pos = pos + k
                if next_pos >= n:
                    continue

                if flat[next_pos] != -1:
                    next_pos = flat[next_pos] - 1 # 0 index

                if next_pos not in visited:
                    visited.add(next_pos)
                    queue.append((next_pos, rolls + 1))

        return -1

    main = snakesAndLadders

class Solution_1061_A(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 1061, 'Medium')

    main = None

    def smallestEquivalentString(self, s1, s2, baseStr):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/lexicographically-smallest-equivalent-string/?envType=daily-question&envId=2025-06-05

        :type s1: str
        :type s2: str
        :type baseStr: str
        :rtype: str
        '''

        groups = []

        for a, b in zip(s1, s2):
            new_group = set([a, b])
            merged_groups = []

            # intersections
            for g in groups:
                if g & new_group:
                    new_group |= g
                    merged_groups.append(g)

            for g in merged_groups:
                groups.remove(g)

            groups.append(new_group)

        small_map = {}
        result = ''
        for c in baseStr:
            if c in small_map.keys():
                result += small_map[c]

            else:
                best = c
                for g in groups:
                    if c in g:
                        best = min(min(g), best)
                        break

                result += best
                small_map[c] = best

        return result

    main = smallestEquivalentString

class Solution_1061_B(Solution):
    def __init__(self):
        super().__init__('ChatGPT', 1061, 'Medium')

    main = None

    def smallestEquivalentString(self, s1, s2, baseStr):
        '''
        Author: ChatGPT
        Link: https://leetcode.com/problems/lexicographically-smallest-equivalent-string/?envType=daily-question&envId=2025-06-05

        :type s1: str
        :type s2: str
        :type baseStr: str
        :rtype: str
        '''

        parent = {chr(i): chr(i) for i in range(ord('a'), ord('z') + 1)}

        def find(c): # finds the min since the min --> own parent
            if parent[c] != c:
                parent[c] = find(parent[c])

            return parent[c]

        def union(a, b):
            rootA, rootB = find(a), find(b) # get the min known now
            if rootA == rootB:
                return

            if rootA < rootB:
                parent[rootB] = rootA
            else:
                parent[rootA] = rootB

        for a, b in zip(s1, s2):
            union(a, b)

        return ''.join(find(c) for c in baseStr)

    main = smallestEquivalentString

class Solution_1432(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 1432, 'Medium')

    main = None

    def maxDiff(self, num):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/max-difference-you-can-get-from-changing-an-integer/?envType=daily-question&envId=2025-06-15
        
        :type num: int
        :rtype: int
        '''

        a = str(num)
        b = str(num)

        for c in a:
            if int(c) < 9:
                a = a.replace(c, '9')
                break

        first = b[0]
        for c in b:
            if c == first:
                if int(c) > 1:
                    b = b.replace(c, '1')
                    break
            else:
                if int(c) > 0:
                    b = b.replace(c, '0')
                    break

        return abs(int(a) - int(b))

    main = maxDiff

class Solution_2131(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 2131, 'Medium')

    def longestPalindrome(self, words):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/longest-palindrome-by-concatenating-two-letter-words/?envType=daily-question&envId=2025-05-25

        :type colors: str
        :type edges: List[List[int]]
        :rtype: int
        '''

        count = {}
        for word in words:
            if word in count:
                count[word] += 1
            else:
                count[word] = 1

        length = 0
        center = False

        for word in list(count.keys()):
            rev = word[::-1]
            if word != rev:
                if rev in count:
                    pairs = min(count[word], count[rev])
                    length += pairs * 4
                    count[word] -= pairs
                    count[rev] -= pairs

            else:
                pairs = count[word] // 2
                length += pairs * 4
                count[word] -= pairs * 2

                if count[word] > 0: # should be odd
                    center = True

        if center:
            length += 2

        return length

    main = longestPalindrome

class Solution_2359(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 2359, 'Medium')

    def closestMeetingNode(self, edges, node1, node2):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/find-closest-node-to-given-two-nodes/?envType=daily-question&envId=2025-05-30

        :type edges: List[int]
        :type node1: int
        :type node2: int
        :rtype: int
        '''

        def distances(node):
            distance = 0
            v = set()
            r = [len(edges) * 10] * len(edges)

            while True:
                if node in v: break
                v.add(node)
                r[node] = distance
                distance += 1
                node = edges[node]
                if node == -1: break

            return r

        d1 = distances(node1)
        d2 = distances(node2)

        argmin = 0
        impossible = True

        for i in range(len(edges)):
            if d1[i] < len(edges) * 10 and d2[i] < len(edges) * 10:
                impossible = False

            if max(d1[i], d2[i]) < max(d1[argmin], d2[argmin]):
                argmin = i

        if impossible: return -1
        return argmin

    main = closestMeetingNode

class Solution_2434(Solution):
    '''
    Plan:
        - get min pos for every i in s
        - if s is empty, put reverse(t)
        - if t is empty, add more s
        - add the end of t while the end of t <= min(s)
    '''

    def __init__(self):
        super().__init__('Kevin Zhu', 2434, 'Medium')

    main = None

    def robotWithString(self, s):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/using-a-robot-to-print-the-lexicographically-smallest-string/?envType=daily-question&envId=2025-06-06

        :type s: str
        :rtype: str
        '''

        if len(s) <= 1:
            return s

        n = len(s)
        stack = []
        c = list(s)
        result = []

        # if at this index there is something smaller afterwards
        suffixes = [''] * n
        suffixes[-1] = s[-1]
        for i in reversed(range(n - 1)):
            suffixes[i] = min(s[i], suffixes[i + 1])

        i = 0 # tracks the current position in s for the suffixes
        while i < n or stack:
            if i < n:
                stack.append(s[i])
                i += 1

            if i == n:
                result.extend(list(reversed(stack)))
                break

            else:
                while stack and (i == n or stack[-1] <= suffixes[i]):
                    result.append(stack.pop())

        return ''.join(result)

    main = robotWithString

class Solution_2616(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 2616, 'Medium')

    main = None

    def minimizeMax(self, nums, p):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/minimize-the-maximum-difference-of-pairs/?envType=daily-question&envId=2025-06-13

        :type nums: List[int]
        :type p: int
        :rtype: int
        '''

        nums = sorted(nums)
        n = len(nums)

        # Edge case: if p is 0, no pairs needed, so difference is 0
        if p == 0:
            return 0

        # smallest diff is 0, largest diff is the max - min
        left = 0
        right = nums[-1] - nums[0]
        ans = right # start with largeest diff

        # Helper function to check if we can form 'p' pairs with max_diff
        def can_form_pairs(max_diff):
            count, i = 0, 0

            while i < n - 1: # the reason why we can just loop through like this is because if it doesn't work, any deviation from the sort will be less efficient
                if nums[i + 1] - nums[i] <= max_diff:
                    count += 1
                    i += 2 # skip used

                else:
                    i += 1

                if count >= p:
                    return True

            return False

        # Binary search, more efficient than just going through all possible min-max differences
        while left <= right:
            mid = left + (right - left) // 2

            if can_form_pairs(mid):
                ans = mid # lhs of mid
                right = mid - 1

            else:
                left = mid + 1 # rhs of mid

        return ans

    main = minimizeMax

class Solution_2929(Solution):

    '''
    This solution just usees the stars and bars problem.
    It also includes exclutions for the usage of limit.
    However, since we multiply by 3, cases like (3, 3, 1) where 3 is over the limit need to be added back in.
    This is because we subtract for child 1, but child 2 has the same case which we subtract 3 times again.
    Then, for cases like (3, 3, 3), we need to subtract again since we added it back in.
    '''

    def __init__(self):
        super().__init__('Kevin Zhu', 2929, 'Medium')

    def distributeCandies(self, n, limit):
            '''
            Author: Kevin Zhu
            Link: https://leetcode.com/problems/distribute-candies-among-children-ii/?envType=daily-question&envId=2025-06-01

            :type n: int
            :type limit: int
            :rtype: int
            '''

            def choose(n, k):
                if k < 0 or k > n:
                    return 0
                if k == 0 or k == n:
                    return 1
                if k == 1:
                    return n
                if k == 2:
                    return n * (n - 1) // 2
                return 0

            # Total ways without restrictions
            total = choose(n + 2, 2)

            # Subtract cases where 1 child exceeds limit
            over1 = 3 * choose(n - (limit + 1) + 2, 2) if n >= limit + 1 else 0

            # Add back cases where 2 children exceed limit
            over2 = 3 * choose(n - 2 * (limit + 1) + 2, 2) if n >= 2 * (limit + 1) else 0

            # Subtract cases where all 3 children exceed limit
            over3 = choose(n - 3 * (limit + 1) + 2, 2) if n >= 3 * (limit + 1) else 0

            return total - over1 + over2 - over3

    main = distributeCandies

class Solution_2929(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 3170, 'Medium')

    main = None

    def clearStars(self, s):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/lexicographically-minimum-string-after-removing-stars/?envType=daily-question&envId=2025-06-07

        :type s: str
        :rtype: str
        '''

        char_indices = [[] for _ in range(26)]  # one list per lowercase letter
        removals = set()

        for j, c in enumerate(s):
            if c == '*':
                for i in range(26):
                    if char_indices[i]:
                        index = char_indices[i].pop()
                        removals |= {index, j} # instead of removal, which changes list indices, just mark as removed
                        break
            else:
                char_indices[ord(c) - ord('a')].append(j)

        return ''.join(s[i] for i in range(len(s)) if i not in removals)

    main = clearStars

class Solution_3372(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 3372, 'Medium')

    def maxTargetNodes(self, edges1, edges2, k):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/maximize-the-number-of-target-nodes-after-connecting-trees-i/?envType=daily-question&envId=2025-05-28

        :type edges1: List[List[int]]
        :type edges2: List[List[int]]
        :type k: int
        :rtype: List[int]
        '''

        def build_adj(edges):
            nodes = {}
            for i, j in edges:
                if i in nodes.keys():
                    nodes[i].append(j)

                else:
                    nodes[i] = [j]

                if j in nodes.keys():
                    nodes[j].append(i)

                else:
                    nodes[j] = [i]

            return nodes

        nodes1 = build_adj(edges1)
        nodes2 = build_adj(edges2)

        def target(node, max_depth, graph):
            result = set()

            def dfs(current, depth):
                if depth > max_depth:
                    return

                if current in result:
                    return

                result.add(current)

                for neighbor in graph.get(current, []):
                    dfs(neighbor, depth + 1)

            dfs(node, 0)
            return result

        max_targets2 = 0
        for node in nodes2:
            reachable = target(node, k - 1, nodes2)
            max_targets2 = max(max_targets2, len(reachable))

        result = []
        for node in nodes1:
            reachable1 = target(node, k, nodes1)
            result.append(len(reachable1) + max_targets2)

        return result

    main = maxTargetNodes

class Solution_3403(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 3403, 'Medium')

    main = None

    def answerString(self, word, numFriends):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/find-the-lexicographically-largest-string-from-the-box-i/?envType=daily-question&envId=2025-06-04

        :type word: str
        :type numFriends: int
        :rtype: str
        '''

        if numFriends == 1: return word

        max_length = len(word) - numFriends + 1
        char = max(word)
        best = ''

        for i, c in enumerate(word):
            if c == char:
                cand = word[i:i + min(max_length, len(word) - i)]
                if cand > best: best = cand

        return best

    main = answerString