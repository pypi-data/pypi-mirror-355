import random as rand

# Operation on lists
def zero(number: int)->list[int]:
    """Creates a list of zeroes with the specified length."""
    return [0]*number

def prod(L: list[int|float], a: int|float)->list[int|float]:
    """Multiplies each element in the list by the given number."""
    return [a*i for i in L]

def addl(*args: list[int|float])->list[int|float]:
    """Adds corresponding elements from multiple lists."""
    if not args:
        return []
    result=zero(max(len(lst) for lst in args))
    for lst in args:
        if type(lst)==list:
            for i in range(len(lst)):
                result[i]+=lst[i]
    return result

def linespace(start: int, end: int, step=1)->list[int|float]:
    """Generates a list of values starting from `start` to `end` with a given step."""
    step=(step).__abs__() if start<end else -(step).__abs__()
    return [i for i in range(start, end+(1 if step>0 else -1), step)]

def array(start: int|float, end: int|float, n: int)->list[int|float]:
    """Generates a list of `n` values evenly spaced between `start` and `end`."""
    if n<=0:
        return []
    return [start+i*(end-start)/n for i in range(n+1)]

def uni(*lists: list)->list:
    """Merges multiple lists into a single list."""
    return [item for lst in lists for item in lst]

def uniwd(*listes: list)->list:
    """Merges multiple lists into a single list, removing duplicates."""
    resultat=[]
    for liste in listes:
        for element in liste:
            if element not in resultat:
                resultat.append(element)
    return resultat

def inter(*listes: list)->list:
    """Finds the intersection of multiple lists."""
    return list(set(listes[0]).intersection(*listes[1:]))

def uniq(L: list)->list:
    """Returns a list with unique elements from the input list."""
    return list(set(L))

def moy(L: list[int|float])->int|float:
    """Calculates the average of a list of numbers.
    
    Raises a ValueError if the list is empty."""
    if len(L)!=0:
        return sum(L)/len(L)
    raise ValueError("The list must not be empty")

def sum_int(start: int, end: int)->int:
    """Returns the sum of all integers in the range from `start` to `end`."""
    return sum(linespace(start, end))

def randl(min: int|float, max: int|float, n: int)->list[int|float]:
    """enerates a list of `n` random integers between `min` and `max`."""
    return [rand.randint(min, max) for i in range(n)]

def shuffle_list(L: list)->list:
    """Returns a new list with the elements of `L` shuffled."""
    L_=L[:]
    rand.shuffle(L_) 
    return L_

def filtrer(L: list, condition: callable)->list:
    """Filters the list `L` by a given condition."""
    return [x for x in L if condition(x)]

def chunk(L: list, n: int)->list[list]:
    """Divides the list `L` into chunks of size `n`.

    Raises a ValueError if `n` is less than 1."""
    if n>=1:
        return [L[i:i+n] for i in range(0, len(L), n)]
    raise ValueError("n must be greater than or equal to 1")

def partition(L: list, condition: callable)->tuple:
    """Splits the list `L` into two sublists based on a condition.

    Raises a TypeError if the condition is not callable."""
    if callable(condition):
        return [x for x in L if condition(x)], [x for x in L if not condition(x)]
    raise TypeError("Condition must be a function")
    
def subindex(L: list, item) -> int:
    """Returns the index of the first sublist in `L` containing the `item`.
    
    Raises a ValueError if the item is not found."""
    for index, i in enumerate(L):
        try:
            if item in i:
                return index
        except TypeError:
            pass
    raise ValueError(f"{item} not found in the list")
