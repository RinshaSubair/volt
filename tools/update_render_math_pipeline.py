import re

def main():
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Define smart repairLatex and safeCollapseBackslashes in JS
    old_pipeline = '''  // 2. Normalize backslashes \\ -> \\ in text nodes
  try {
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
    let textNode;
    const nodesToProcess = [];
    while(textNode = walker.nextNode()){
      const parent = textNode.parentElement;
      if(!parent) continue;
      const tag = parent.tagName.toLowerCase();
      if(['script', 'style', 'code', 'pre', 'svg', 'option', 'textarea'].includes(tag)) continue;
      if(parent.closest('.katex, .no-math, .formula-box')) continue;
      
      let val = textNode.nodeValue;
      if(val && val.includes('\\\\')){
        nodesToProcess.push(textNode);
      }
    }

    nodesToProcess.forEach(node => {
      node.nodeValue = node.nodeValue.replace(/\\\\/g, '\\\\');
    });
  } catch(e) {}'''

    new_pipeline = '''  // 2. Safe normalization of backslashes (preserving matrix row breaks \\\\)
  try {
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
    let textNode;
    const nodesToProcess = [];
    while(textNode = walker.nextNode()){
      const parent = textNode.parentElement;
      if(!parent) continue;
      const tag = parent.tagName.toLowerCase();
      if(['script', 'style', 'code', 'pre', 'svg', 'option', 'textarea'].includes(tag)) continue;
      if(parent.closest('.katex, .no-math, .formula-box')) continue;
      
      let val = textNode.nodeValue;
      if(val && val.includes('\\\\')){
        nodesToProcess.push(textNode);
      }
    }

    nodesToProcess.forEach(node => {
      const v = node.nodeValue;
      if(v.includes('bmatrix') || v.includes('pmatrix') || v.includes('vmatrix') || v.includes('cases') || v.includes('align')){
        node.nodeValue = v.replace(/\\\\\\\\/g, '\\\\');
      } else {
        node.nodeValue = v.replace(/\\\\/g, '\\\\');
      }
    });
  } catch(e) {}'''

    if old_pipeline in html:
        html = html.replace(old_pipeline, new_pipeline)
        print("Updated text node backslash normalization in renderMath!")
    else:
        print("Could not find exact old_pipeline block, applying pattern substitution...")
        html = html.replace(r"node.nodeValue = node.nodeValue.replace(/\\\\/g, '\\');", r"const v = node.nodeValue; node.nodeValue = (v.includes('bmatrix') || v.includes('pmatrix') || v.includes('cases')) ? v.replace(/\\\\\\\\/g, '\\\\') : v.replace(/\\\\/g, '\\\\');")

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("Pipeline update finished!")

if __name__ == '__main__':
    main()
