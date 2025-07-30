from .Solution import Solution

class Solution_2016_A(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 2016, 'Easy')

    main = None

    def maximumDifference(self, nums):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/maximum-difference-between-increasing-elements/?envType=daily-question&envId=2025-06-16

        :type nums: List[int]
        :rtype: int
        '''

        max_diff = -1
        for i in range(1, len(nums)):
            max_diff = max(nums[i] - min(nums[:i]), max_diff)

        return max_diff if max_diff > 0 else -1

    main = maximumDifference

class Solution_2016_B(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 2016, 'Easy')

    main = None

    def maximumDifference(self, nums):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/maximum-difference-between-increasing-elements/?envType=daily-question&envId=2025-06-16

        :type nums: List[int]
        :rtype: int
        '''

        max_diff = -1
        min_val = nums[0]

        for i in range(1, len(nums)):
            if nums[i] > min_val:
                max_diff = max(max_diff, nums[i] - min_val)

            else:
                min_val = nums[i]

        return max_diff if max_diff > 0 else -1

    main = maximumDifference

class Solution_2566(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 2566, 'Easy')

    main = None

    def minMaxDifference(self, num):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/maximum-difference-by-remapping-a-digit/?envType=daily-question&envId=2025-06-14

        :type num: int
        :rtype: int
        '''

        a = str(num)
        b = str(num)

        for c in a:
            if int(c) < 9:
                a = a.replace(c, '9')
                break

        for c in b:
            if int(c) > 0:
                b = b.replace(c, '0')
                break

        return abs(int(a) - int(b))

    main = minMaxDifference

class Solution_2894(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 2894, 'Easy')

    def differenceOfSums(self, n, m):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/divisible-and-non-divisible-sums-difference/?envType=daily-question&envId=2025-05-27

        :type n: int
        :type m: int
        :rtype: int
        '''
        num = 0
        for i in range(n + 1):
            num += i if i % m != 0 else -i

        return num

    main = differenceOfSums

class Solution_2942(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 2942, 'Easy')

    def findWordsContaining(self, words, x):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/find-words-containing-character/?envType=daily-question&envId=2025-05-24

        :type words: List[str]
        :type x: str
        :rtype: List[int]
        '''

        indices = []
        for i in range(len(words)):
            if x in words[i]: indices.append(i)

        return indices

    main = findWordsContaining

class Solution_3423(Solution):

    '''
    Thank you LeetCode for an easy problem today! (especially after yesterday...)
    '''

    def __init__(self):
        super().__init__('Kevin Zhu', 3423, 'Easy')

    main = None

    def maxAdjacentDistance(self, nums):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/maximum-difference-between-adjacent-elements-in-a-circular-array/?envType=daily-question&envId=2025-06-12

        :type nums: List[int]
        :rtype: int
        '''

        nums.append(nums[0])
        diff = [abs(nums[i + 1] - nums[i]) for i in range(len(nums)) if i < len(nums) - 1]
        return max(diff)

class Solution_3442(Solution):
    def __init__(self):
        super().__init__('Kevin Zhu', 3442, 'Easy')

    main = None

    def maxDifference(self, s):
        '''
        Author: Kevin Zhu
        Link: https://leetcode.com/problems/maximum-difference-between-even-and-odd-frequency-i/description/?envType=daily-question&envId=2025-06-10

        :type s: str
        :rtype: int
        '''

        g = [0] * 26

        for c in s: g[ord(c) - ord('a')] += 1

        a1 = 0
        a2 = len(s)

        for i in g:
            if i == 0: continue

            if i % 2 == 1 and i > a1:
                a1 = i

            if i % 2 == 0 and i < a2:
                a2 = i

        return a1 - a2

    main = maxDifference

