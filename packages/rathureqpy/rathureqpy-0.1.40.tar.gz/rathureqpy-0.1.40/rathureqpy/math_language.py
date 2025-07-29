import re

# Latex
exponent: str = str.maketrans('0123456789abcdefghijklmnopqrstuvwxyz+-=',
                              '⁰¹²³⁴⁵⁶⁷⁸⁹ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖˤʳˢᵗᵘᵛʷˣʸᶻ⁺⁻⁼')
index:str = str.maketrans('0123456789abeijklmnoprstuvx+-=()',
                          '₀₁₂₃₄₅₆₇₈₉ₐᵦₑᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ₊₋₌₍₎')
letters:str='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ' 

def lat(expr:str)->str:
    """Converts a simple LaTeX-like expression into Unicode math characters.
    
    Transforms exponents, indices, square roots, sums, products, integrals, and fractions."""
    expr=re.sub(r'(\w)\^(\w+)', lambda m: m.group(1) + m.group(2).translate(exponent), expr)
    expr=re.sub(r'(\w)_([0-9n+-=()]+)', lambda m: m.group(1) + m.group(2).translate(index), expr)
    expr=re.sub(r'sqrt\(([^)]+)\)', r'√(\1)', expr)
    expr=re.sub(r'sum\{(\w)=(\d+)\}\^(\w+)', lambda m: f'∑{m.group(1).translate(index)}₌{m.group(2).translate(index)}{m.group(3).translate(exponent)}', expr)
    expr=re.sub(r'prod\{(\w)=(\d+)\}\^(\w+)', lambda m: f'∏{m.group(1).translate(index)}₌{m.group(2).translate(index)}{m.group(3).translate(exponent)}', expr)
    expr=re.sub(r'\bint\b', '∫', expr)
    expr=re.sub(r'frac{([^{}]+)}{([^{}]+)}',lambda m: m.group(1).translate(exponent) + '⁄' + m.group(2).translate(index),expr)
    return expr

def symbol(sym:str)->str:
    """Returns the Unicode math symbol corresponding to the given LaTeX command.
    
    If the command is not recognized, returns '[unknown: command]'."""
    return {'emptysetalt':'ø','emptysetAlt':'Ø','kannada':'ೲ','infty':'∞','O':'Ø','partial':'∂','nabla':'∇','forall':'∀','exists':'∃','in':'∈','notin':'∉','subset':'⊂','subseteq':'⊆','supset':'⊃','supseteq':'⊇','emptyset':'∅','approx':'≈','neq':'≠','leq':'≤','geq':'≥','times':'×','div':'÷','cdot':'⋅','perp':'⊥','mapsto':'↦'}.get(sym, f'[unknown: {sym}]')

def dot(text: str) -> str:
    """Returns the input string `text` with a dot placed above each character."""
    return ''.join(char + '\u0307' for char in text)

def vec(text: str) -> str:
    """Returns the input string `text` with a bar placed above each character."""
    return ''.join(char + '\u0305' for char in text)

def greek(expr:str)->str:
    """Converts a Greek letter name into its corresponding Unicode symbol.
    
    Returns an empty string if the letter name is not recognized."""
    return  {'alpha': 'α','beta': 'β','gamma': 'γ','delta': 'δ','epsilon': 'ε','zeta': 'ζ','heta': 'η','theta': 'θ','iota': 'ι','kappa': 'κ','lambda': 'λ','mu': 'μ','nu': 'ν','xi': 'ξ','omicron': 'ο','pi': 'π','rho': 'ρ','sigma': 'σ','tau': 'τ','upsilon': 'υ','phi': 'ϕ','chi': 'χ','psi': 'ψ','omega': 'ω','Gamma': 'Γ','Delta': 'Δ','Theta': 'Θ','Lambda': 'Λ','Xi': 'Ξ','Pi': 'Π','Sigma': 'Σ','Phi': 'Φ','Psi': 'Ψ','Omega': 'Ω'}.get(expr, '')

def italic(text:str) -> str:
    """Converts the input string `text` to italic Unicode characters.
    
    Only letters a-z and A-Z are transformed."""
    tex=''
    for char in text:
        if char in letters:
            tex+='𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡'[letters.index(char)]
    return tex

def bold(text:str) -> str:
    """Converts the input string `text` to bold Unicode characters.
    
    Only letters a-z and A-Z are transformed."""
    tex=''
    for char in text:
        if char in letters:
            tex+='𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭'[letters.index(char)]
    return tex

def mathbb(text:str) -> str:
    """Converts the input string `text` to mathematical double-struck Unicode characters.
    
    Only letters a-z and A-Z are transformed."""
    tex=''
    for char in text:
        if char in letters:
            tex+='𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ'[letters.index(char)]
    return tex

def cursive(text:str) -> str:
    """Converts the input string `text` to cursive Unicode characters.
    
    Only letters a-z and A-Z are transformed."""
    tex=''
    for char in text:
        if char in letters:
            tex+='𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓧𝓨𝓩'[letters.index(char)]
    return tex
