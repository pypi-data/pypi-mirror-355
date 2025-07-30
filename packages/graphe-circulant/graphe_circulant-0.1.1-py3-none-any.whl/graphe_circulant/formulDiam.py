def PE_SUP(a, b):
    """Retourne a/b si a est divisible par b, 
       sinon retourne (x/p) + 1.
    """
    return a // b if a % b == 0 else (a // b) + 1


def FormulDiam(n, s):
    # n = q.s + r
    q = n // s
    r = n % s

    """ I """
    if r == 0:
        return (q + s - 1) // 2 , False
    

    """ II """
    if q > r:
        # cas 1 : n pair et s impair
        if n % 2 == 0 and s % 2 == 1:
            return PE_SUP(q, 2) + (s + 1) // 2 - (min(PE_SUP(r, 2), PE_SUP(s - r + 1, 2))) , False
        
        # cas 2 : n pair et s pair
        if n % 2 == 0 and s % 2 == 0:
            if r <= 2 * PE_SUP(s - 2, 4):
                return PE_SUP(q, 2) + (s - r) // 2 , False
            return q // 2 + r // 2 , False
        
        # cas 3 : n impair et s impair
        if n % 2 == 1 and s % 2 == 1:
            return PE_SUP(q, 2) + (s + 1) // 2 - (min(PE_SUP(r + 1, 2), PE_SUP(s - r + 2, 2))) , False
        
        # cas 4 : n impair et s pair
        if n % 2 == 1 and s % 2 == 0:
            if  r == 1 or r == s - 1:
                return PE_SUP(q, 2) + (s - 2) // 2 , False
            if 3 <= r <= 2 * PE_SUP(s, 4) - 1:
                return (q // 2) + (s - r + 1) // 2 , False
            return PE_SUP(q, 2) + (r - 1) // 2 , False
    
    """ III le cas de r >= q """
    # n = q.s + r    si r >= q  ===> s = a.r + b
    a = s // r
    b = s % r

    p0 = (q + r) // 2
    p1 = (r - b + (a + 1) * q + 1) // 2
    p2 = (r + b + (a - 1) * q + 1) // 2
    p3 = (b + a * q + 1) // 2
    p4 = ((r + b) * (a * q - q + 1))
    e = min(max(p1, p3), max(p0, p2))

    if q <= r and b <= a * q + 1:
        if p1 == p2 and p4 % 2 == 1:
            return p1 - 1 , False
        return e , False
    
    """All n and s"""
    borne1 = max((n // s) + 1, n - (n // s) * s - 2, (n // s) + 1 * s - n - 1)
    borne2 = (n + 2) // 4
    borne3 = ((n // 2)) // s + PE_SUP(s , 2)

    return  min(borne1, borne2, borne3) , True