import math as m
from .list_utils import filtrer 
from .logic_utils import divisor_list

# Constants
pi: float = 3.141592653589793
e: float = 2.718281828459045
tau: float = 2 * pi

# Mathematical operations
def abs(x: int|float)->int:
    """Returns the absolute value of `x`."""
    return x.__abs__()

def cos(x: int|float)->int|float:
    """Returns the cosine of `x`."""
    return m.cos(x)

def sin(x: int|float)->int|float:
    """Returns the sine of `x`."""
    return m.sin(x)

def log(x: int|float, base=e)->int|float:
    """Returns the logarithm of `x` with the specified `base`.

    Raises a ValueError if `x` is less than or equal to 0."""
    if x>0:
        return m.log(x, base)
    raise ValueError('x must be greater than 0')

def exp(x: int|float)->int|float:
    """Returns `e` raised to the power of `x`."""
    return m.exp(x)

def sqrt(x: int|float)->int|float:
    """Returns the square root of `x`.

    Raises a ValueError if `x` is negative."""
    if x>=0:
        return m.sqrt(x)
    raise ValueError('x must be greater than or equal to 0')

def facto(n: int)->int:
    """Returns the factorial of `n`.

    Returns 1 for negative `n`."""
    return m.factorial(n) if n >= 0 else 1

def floor(x: int|float)->int:
    """Returns the largest integer less than or equal to `x`."""
    if x>=0:
        return int(x)
    return int(x)-1

def ceil(x: int|float)->int:
    """Returns the smallest integer greater than or equal to `x`."""
    if x>=0:
        return int(x)+1
    return int(x)
    
def rint(x:int|float)->int:
    """Rounds `x` to the nearest integer."""
    if abs(x-floor(x))<=abs(x-ceil(x)):
        return floor(x)
    return ceil(x)
    
def gcd(a: int, b: int)->int:
    """Returns the greatest common divisor of `a` and `b`."""
    while a!=0 and b!=0: a, b=b, a%b
    return a

def lcm(a: int, b: int)->int:
    """Returns the least common multiple of `a` and `b`."""
    return abs(a*b)//gcd(a, b) if a and b else 0

def is_prime(n: int)->bool:
    """Returns True if `n` is a prime number, otherwise False."""
    if n<=1:
        return False
    for i in range(2, int(m.sqrt(n))+1):
        if n%i==0:
            return False
    return True

def integ(f, a, b, N):
    """Returns the integral of f from a to b using the trapezoidal rule.

    Swaps a and b if a > b, and adjusts the sign accordingly."""
    if a<=b:
        return (b-a)/N*sum([1/2*(f(a+k*(b-a)/N) + f(a+(k+1)*(b-a)/N)) for k in range(N)])
    a, b=b, a
    return -(b-a)/N*sum([1/2*(f(a+k*(b-a)/N) + f(a+(k+1)*(b-a)/N)) for k in range(N)])

# Statistical measures
def variance(L: list[int])->int|float:
    """ Returns the variance of the list `L`.

    Returns None if the list is empty."""
    if not L:
        return None
    mean=sum(L)/len(L)
    var=sum((x-mean)**2 for x in L)/len(L)
    return var

def ecart_type(L: list[int])->int|float:
    """Returns the standard deviation of the list `L`.

    Returns None if the list is empty or variance is None."""
    var=variance(L)
    if var is None:
        return None
    return m.sqrt(var)

def mediane(L: list[int])->int|float:
    """Returns the median of the list `L`.

    Returns None if the list is empty."""
    if not L:
        return None
    L_sorted=sorted(L)
    if len(L_sorted)%2==1:
        return L_sorted[len(L_sorted)//2]
    else:
        return (L_sorted[len(L_sorted)//2-1]+L_sorted[len(L_sorted)//2])/2

# Mathematical utilities
def decomp(n: int)->list[tuple[int, int]]:
    """Returns the prime factorization of `n` as a list of tuples `(prime, count)`."""
    div=[]
    while not is_prime(n):
        div.append(divisor_list(n)[1])
        n//=divisor_list(n)[1]
    div.append(n)
    return [(i, div.count(i)) for i in list(set(div))]

def list_prime(n:int)->list[int]:
    """Returns a list of all prime numbers up to `n`."""
    return filtrer([i for i in range(n+1)], is_prime)

def pascal_row(n: int)->list[int]:
    """Returns the `n`th row of Pascal's triangle.

    Raises a ValueError if `n` is less than 1."""
    if n>=1:
        row=[1]
        for i in range(n):  
            row=[1]+[row[j]+row[j+1] for j in range(len(row)-1)]+[1]
        return row
    raise ValueError("n must be greater than or equal to 1")
