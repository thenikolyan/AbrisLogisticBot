class cycle:
    def __init__(self, c):
        self.count = c
        self.to_list = c
        self.ind = -1

    def __next__(self):
        self.ind += 1
        if self.ind>=len(self.count):
            self.ind = 0
        return self.count[self.ind]

    def previous(self):
        self.ind -= 1
        if self.ind < 0:
            self.ind = len(self.count)-1
        return self.count[self.ind]
    