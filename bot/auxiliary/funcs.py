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
    

def distance(La1, Lo1, La2, Lo2):
    from math import radians, cos, sin, asin, sqrt

    Lo1 = radians(Lo1)
    Lo2 = radians(Lo2)
    La1 = radians(La1)
    La2 = radians(La2)

    D_Lo = Lo2 - Lo1
    D_La = La2 - La1
    P = sin(D_La / 2) ** 2 + cos(La1) * cos(La2) * sin(D_Lo / 2) ** 2

    Q = 2 * asin(sqrt(P))

    R_km = 6371


    return (round(Q * R_km,2))