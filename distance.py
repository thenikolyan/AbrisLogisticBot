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

print(distance(40.7128,-74.0060,31.9686,  -99.9018))