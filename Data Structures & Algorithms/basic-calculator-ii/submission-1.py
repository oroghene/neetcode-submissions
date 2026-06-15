class Solution:
    def calculate(self, s: str) -> int:
        total = prev = num = 0
        n = len(s)
        i = 0
        op = '+'

        while i <= n:
            c = s[i] if i < n else '+'
            if c == ' ':
                i += 1
                continue
            
            if '0' <= c <= '9':
                num = num * 10 + (ord(c) - ord('0'))
            else:
                if op == '+':
                    total += prev
                    prev = num
                elif op == '-':
                    total += prev
                    prev = -num
                elif op == '*':
                    prev *= num
                else:
                    if prev < 0:
                        prev = -(-prev // num)
                    else:
                        prev = prev // num
                op = c
                num = 0
            i += 1
        total += prev
        return total