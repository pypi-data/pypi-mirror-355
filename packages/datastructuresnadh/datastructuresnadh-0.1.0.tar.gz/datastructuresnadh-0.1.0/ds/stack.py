""" Stack implementation """


class Stack:
    def __init__(self, max_size:int=10) -> None:
        self.stack :list= [None] * max_size  # Initialize stack with fixed size
        self.top :int= -1  # Use -1 to indicate an empty stack
        self.max_size :int= max_size

    def push_ele(self, v:int=0) -> None:
        if self.top == self.max_size - 1:
            raise Exception("Stack Overflow")
        self.top += 1
        self.stack[self.top] = v

    def pop_ele(self) -> int:
        if self.top == -1:
            raise Exception("Stack Underflow")
        v = self.stack[self.top]
        self.stack[self.top] = None  # Clear the value (optional)
        self.top -= 1
        return v

    def peek(self) -> int:
        if self.top == -1:
            raise Exception("Stack Underflow")
        return self.stack[self.top]

    def printstack(self) -> list:
        if self.top == -1:
            raise Exception("Stack Underflow")
        return self.stack[: self.top + 1]  # Return only the valid elements