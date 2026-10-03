import re

def main():
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Locate repairLatex function definition in html
    start = html.find('function repairLatex(')
    if start == -1:
        print("Could not find repairLatex function!")
        return

    end = html.find('}\n\nfunction renderMath', start)
    if end == -1:
        end = html.find('}', start + 300)

    print("Found repairLatex function bounds:", start, "to", end)

    new_repair_latex = '''function repairLatex(str){
  if(!str) return '';
  let s = str;

  // 1. Strip redundant outer math delimiters if passed directly to KaTeX
  s = s.trim();
  if(s.startsWith('$$') && s.endsWith('$$')) s = s.slice(2, -2).trim();
  else if(s.startsWith('\\[') && s.endsWith('\\]')) s = s.slice(2, -2).trim();
  else if(s.startsWith('\\(') && s.endsWith('\\)')) s = s.slice(2, -2).trim();

  // 2. Remove unescaped internal $ signs inside math string
  s = s.replace(/(?<!\\)\$/g, '');

  // 3. Fix unescaped & outside matrix/cases environments
  if(!/(bmatrix|pmatrix|vmatrix|cases|matrix|align|CD)/.test(s)){
    s = s.replace(/(?<!\\)&/g, '\\&');
  }

  // 4. Fix unescaped % signs
  s = s.replace(/(?<!\\)%/g, '\\%');

  // 5. Fix control character artifacts
  s = s.replace(/\\x09ext/g, '\\\\text')
       .replace(/\\x09imes/g, '\\\\times')
       .replace(/\\x09heta/g, '\\\\theta')
       .replace(/\\x09au/g, '\\\\tau')
       .replace(/\\x09an/g, '\\\\tan')
       .replace(/\\x09anh/g, '\\\\tanh')
       .replace(/\\x09ilde/g, '\\\\tilde')
       .replace(/\\x09op/g, '\\\\top')
       .replace(/\\x09o/g, '\\\\to')
       .replace(/\\x0c/g, '\\\\f')
       .replace(/\\x08/g, '\\\\b')
       .replace(/\\x07/g, '\\\\a')
       .replace(/\\x0b/g, '\\\\v')
       .replace(/\\x09/g, '\\\\t');

  return s;
}'''

    old_func = html[start:end+1]
    html = html.replace(old_func, new_repair_latex)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("repairLatex function updated in html!")

if __name__ == '__main__':
    main()
