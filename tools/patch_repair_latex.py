import re

def main():
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    start = html.find('function repairLatex(str){')
    if start == -1:
        print("Could not find repairLatex!")
        return

    end = html.find('function renderMath(container){', start)
    if end == -1:
        print("Could not find renderMath!")
        return

    new_repair_latex = '''function repairLatex(str){
  if(!str) return '';
  let s = str.trim();

  // 1. Clean nested or duplicate delimiters passed by renderMathInElement
  s = s.replace(/\\\\\\]\\s*=\\s*\\\\\\[/g, ' = ');
  s = s.replace(/\\\\\\]\\s*\\\\\\[/g, ' ');
  s = s.replace(/\\$\\$\\s*\\$\\$/g, '');
  s = s.replace(/\\$\\$\\s*\$/g, '');
  s = s.replace(/\\$\\$$/g, '').replace(/^\\$\\$/g, '');
  s = s.replace(/\\\\\\]$/g, '').replace(/^\\\\\\[/g, '');
  s = s.replace(/\\\\\\\)$/g, '').replace(/^\\\\\\\(/g, '');

  // 2. Strip any unescaped single $ signs inside math string
  s = s.replace(/(?<!\\\\)\\$/g, '');

  // 3. Fix unescaped & outside matrix/cases
  if(!/(bmatrix|pmatrix|vmatrix|cases|matrix|align|CD)/.test(s)){
    s = s.replace(/(?<!\\\\)&/g, '\\\\&');
  }

  // 4. Fix unescaped %
  s = s.replace(/(?<!\\\\)%/g, '\\\\%');

  // 5. Fix control character artifacts
  s = s.replace(/\\x09ext/g, '\\\\text')
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
       .replace(/\\x09/g, '\\\\t');

  return s;
}

'''

    html = html[:start] + new_repair_latex + html[end:]

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Updated repairLatex in html successfully!")

if __name__ == '__main__':
    main()
