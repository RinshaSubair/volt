import re

def main():
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Replace repairLatex implementation safely
    old_start = html.find('function repairLatex(str){')
    if old_start == -1:
        print("Could not find function repairLatex!")
        return

    old_end = html.find('function renderMath(container){', old_start)
    if old_end == -1:
        print("Could not find function renderMath!")
        return

    new_repair_latex = '''function repairLatex(str){
  if(!str) return "";
  let s = str
    // JS escape artifacts from template literals and string evaluation
    .replace(/\\x09ext/g, '\\\\text')
    .replace(/\\x09imes/g, '\\\\times')
    .replace(/\\x09heta/g, '\\\\theta')
    .replace(/\\x09au/g, '\\\\tau')
    .replace(/\\x09an/g, '\\\\tan')
    .replace(/\\x09anh/g, '\\\\tanh')
    .replace(/\\x09ilde/g, '\\\\tilde')
    .replace(/\\x09op/g, '\\\\top')
    .replace(/\\x09o\\b/g, '\\\\to')
    .replace(/\\x0crac/g, '\\\\frac')
    .replace(/\\x0crall/g, '\\\\forall')
    .replace(/\\x08egin/g, '\\\\begin')
    .replace(/\\x08eta/g, '\\\\beta')
    .replace(/\\x08ar(?=[{\\s_A-Za-z0-9])/g, '\\\\bar')
    .replace(/\\x08ullet/g, '\\\\bullet')
    .replace(/\\x07lpha/g, '\\\\alpha')
    .replace(/\\x07pprox/g, '\\\\approx')
    .replace(/\\x07ngle/g, '\\\\angle')
    .replace(/\\x0bec/g, '\\\\vec')
    .replace(/\\x08/g, '\\\\b')
    .replace(/\\x0c/g, '\\\\f')
    .replace(/\\x0b/g, '\\\\v')

    .replace(/\\r/g, '')
    .replace(/[\\n\\r]ight\\b/g, '\\\\right')
    .replace(/[\\n\\r]ho\\b/g, '\\\\rho')
    .replace(/[\\n\\r]rightarrow\\b/g, '\\\\rightarrow')
    .replace(/\\\\right\\b/g, '\\\\right')
    .replace(/\\\\rho\\b/g, '\\\\rho')

    // Escape & inside \\text{...}
    .replace(/\\\\text\\{([^}]+)\\}/g, function(m, content) {
      return '\\\\text{' + content.replace(/(?<!\\\\)&/g, '\\\\&') + '}';
    })

    // Escape unescaped % in math expressions
    .replace(/(?<!\\\\)%/g, '\\\\%')

    // Fix \\right} -> \\right\\}
    .replace(/\\\\right\\}/g, '\\\\right\\\\}')
    .replace(/\\\\right\\s*\\n?\\s*\\\\ceil/g, '\\\\right\\\\rceil');

  // Fix double backslash in \\end{\\bmatrix} or \\begin{\\bmatrix}
  s = s.replace(/\\\\(begin|end)\\{\\\\*(bmatrix|pmatrix|vmatrix|matrix|cases)\\}/g, '\\\\$1{$2}');

  // Convert inline \\( \\begin{env} ... \\end{env} \\) or $ \\begin{env} ... \\end{env} $ to display mode \\[ \\begin{env} ... \\end{env} \\]
  s = s.replace(/(?:\\\\\\(|\\$)\\s*(\\\\begin\\{(?:cases|bmatrix|pmatrix|vmatrix|matrix|align|array)\\}[\\s\\S]*?\\\\end\\{(?:cases|bmatrix|pmatrix|vmatrix|matrix|align|array)\\})\\s*(?:\\\\\\)|\\$)/g, '\\\\[ $1 \\\\]');

  // Wrap un-delimited \\begin{env} ... \\end{env} in \\[ ... \\]
  s = s.replace(/(?<!\\\\\\[|\\\\\\(\\s*|\\$\\$\\s*|\\$\\s*)(\\\\begin\\{(?:cases|bmatrix|pmatrix|vmatrix|matrix|align|array)\\}[\\s\\S]*?\\\\end\\{(?:cases|bmatrix|pmatrix|vmatrix|matrix|align|array)\\})(?!\\s*\\\\\\]|\\s*\\\\\\)|\\s*\\$\\$|\\s*\\$)/g, '\\\\[ $1 \\\\]');

  return s;
}

'''

    html = html[:old_start] + new_repair_latex + html[old_end:]

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Updated repairLatex successfully!")

if __name__ == '__main__':
    main()
