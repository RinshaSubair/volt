import re, json

def repair_latex(str_val):
    if not str_val: return ''
    str_val = str_val.replace('\\\\', '\\')
    str_val = re.sub(r'\x09ext', r'\\text', str_val)
    str_val = re.sub(r'\x09imes', r'\\times', str_val)
    str_val = re.sub(r'\x09heta', r'\\theta', str_val)
    str_val = re.sub(r'\x09au', r'\\tau', str_val)
    str_val = re.sub(r'\x09an', r'\\tan', str_val)
    str_val = re.sub(r'\x09anh', r'\\tanh', str_val)
    str_val = re.sub(r'\x09ilde', r'\\tilde', str_val)
    str_val = re.sub(r'\x09op', r'\\top', str_val)
    str_val = re.sub(r'\x09o\b', r'\\to', str_val)
    str_val = re.sub(r'\x0crac', r'\\frac', str_val)
    str_val = re.sub(r'\x0crall', r'\\forall', str_val)
    str_val = re.sub(r'\x08egin', r'\\begin', str_val)
    str_val = re.sub(r'\x08eta', r'\\beta', str_val)
    str_val = re.sub(r'\x08ar', r'\\bar', str_val)
    str_val = re.sub(r'\x08ullet', r'\\bullet', str_val)
    str_val = re.sub(r'\x07lpha', r'\\alpha', str_val)
    str_val = re.sub(r'\x07pprox', r'\\approx', str_val)
    str_val = re.sub(r'\x07ngle', r'\\angle', str_val)
    str_val = re.sub(r'\x0bec', r'\\vec', str_val)
    str_val = re.sub(r'\x08', r'\\b', str_val)
    str_val = re.sub(r'\x0c', r'\\f', str_val)
    str_val = re.sub(r'\x0b', r'\\v', str_val)
    str_val = str_val.replace('\r', '')
    str_val = re.sub(r'[\n\r]ight\b', r'\\right', str_val)
    str_val = re.sub(r'[\n\r]ho\b', r'\\rho', str_val)
    str_val = re.sub(r'[\n\r]rightarrow\b', r'\\rightarrow', str_val)
    str_val = re.sub(r'\\right\b', r'\\right', str_val)
    str_val = re.sub(r'\\rho\b', r'\\rho', str_val)
    str_val = re.sub(r'(?<!\\)\b(left)(?=[(\[{|.\\])', r'\\\g<1>', str_val)
    str_val = re.sub(r'(?<!\\)\b(right)(?=[)\]}|.\\])', r'\\\g<1>', str_val)
    str_val = re.sub(r'(?<!\\)\bparallel\b(?!\})', r'\\parallel', str_val)
    kw_pat = r'(?<!\\)\b(overline|bar|widehat|tilde|vec|hat|dot|ddot|frac|text|times|theta|tau|rho|rightarrow|leftarrow|quad|qquad|implies|cdot|pm|mp|approx|infty|omega|Omega|pi|mu|alpha|beta|delta|Delta|partial|sum|int|sqrt|sigma|bmatrix|pmatrix|vmatrix|matrix)\b'
    str_val = re.sub(kw_pat, r'\\\g<1>', str_val)
    str_val = re.sub(r'(?<!\\)(end|begin)\{', r'\\\g<1>{', str_val)
    return str_val

# Test expressions from Part 6
test_exprs = [
    'e = (v \\times B) \\cdot l = Blv \\sin \\theta',
    'R_a = \\text{lap} \\times \\frac{Z}{A}',
    '\\frac{V_1}{V_2} = \\frac{N_1}{N_2}',
    'P = \\sqrt{3} V_L I_L \\cos \\phi',
    '\\tau = K_t \\phi I_a',
    'E_b = V - I_a R_a',
    'f = \\frac{P N}{120}',
    'S = P + jQ = V I^*',
    '\\eta = \\frac{P_{out}}{P_{in}} \\times 100\\%',
    '\\vec{E} = -\\nabla V',
    'Z = \\sqrt{R^2 + (X_L - X_C)^2}',
    'I_c = \\frac{V_c}{X_c} = \\omega C V_c',
    '\\alpha = \\frac{\\beta}{1 + \\beta}',
    'A_v = -\\frac{R_C}{r_e}',
    'H(s) = \\frac{\\omega_0^2}{s^2 + \\frac{\\omega_0}{Q}s + \\omega_0^2}'
]

for idx, expr in enumerate(test_exprs, 1):
    fixed = repair_latex(expr)
    has_raw_unhandled = any(c in fixed for c in ['\x09', '\x0c', '\x08', '\x07', '\x0b'])
    print(f'Expr {idx}: fixed=\"{fixed}\" | Bad Control Chars: {has_raw_unhandled}')
