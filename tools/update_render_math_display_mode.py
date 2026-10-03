import re

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Update unrenderedNodes loop in renderMath
    old_loop = '''    unrenderedNodes.forEach(node => {
      const p = node.parentElement;
      if(!p) return;
      let text = node.nodeValue;
      text = text.replace(/\\\\/g, '\\\\');
      const span = document.createElement('span');
      try {
        katex.render(repairLatex(text), span, { displayMode: false, throwOnError: false, output: 'html' });
        p.replaceChild(span, node);
      } catch(err) {}
    });'''

    new_loop = '''    unrenderedNodes.forEach(node => {
      const p = node.parentElement;
      if(!p) return;
      let text = node.nodeValue;
      const fixedText = repairLatex(text);
      const isDisplay = fixedText.includes('bmatrix') || fixedText.includes('pmatrix') || fixedText.includes('vmatrix') || fixedText.includes('cases') || fixedText.includes('align') || fixedText.includes('\\\\[');
      const span = document.createElement(isDisplay ? 'div' : 'span');
      try {
        katex.render(fixedText, span, { displayMode: isDisplay, throwOnError: false, output: 'html' });
        p.replaceChild(span, node);
      } catch(err) {}
    });'''

    if old_loop in html:
        html = html.replace(old_loop, new_loop)
        print("Updated unrenderedNodes loop in renderMath!")
    else:
        print("Pattern substitution for unrenderedNodes...")
        html = re.sub(
            r'unrenderedNodes\.forEach\(node\s*=>\s*\{[\s\S]*?katex\.render\(repairLatex\(text\),\s*span,\s*\{\s*displayMode:\s*false[\s\S]*?\}\);\s*\}',
            '''unrenderedNodes.forEach(node => {
      const p = node.parentElement;
      if(!p) return;
      let text = node.nodeValue;
      const fixedText = repairLatex(text);
      const isDisplay = fixedText.includes('bmatrix') || fixedText.includes('pmatrix') || fixedText.includes('vmatrix') || fixedText.includes('cases') || fixedText.includes('align') || fixedText.includes('\\\\[');
      const span = document.createElement(isDisplay ? 'div' : 'span');
      try {
        katex.render(fixedText, span, { displayMode: isDisplay, throwOnError: false, output: 'html' });
        p.replaceChild(span, node);
      } catch(err) {}
    });''',
            html
        )

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("renderMath displayMode patch applied successfully!")

if __name__ == '__main__':
    main()
