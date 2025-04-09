class alist:
    items: list
    pos: int

    def __init__(self, *items):
        self.items = items
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.pos < len(self.items):
            return self.items[self.pos]
        else:
            raise StopIteration

