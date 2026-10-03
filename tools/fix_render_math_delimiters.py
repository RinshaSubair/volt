import re

def main():
    print("Reading eee-platform.html...")
    with open('eee-platform.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Locate renderMathInElement options in html
    start = html.find('renderMathInElement(container, {')
    if start == -1:
        print("Could not find renderMathInElement call!")
        return

    end = html.find('preProcess: function(mathStr){', start)
    if end == -1:
        print("Could not find preProcess function!")
        return

    new_delimiters = '''renderMathInElement(container, {
        delimiters: [
          {left: "$$", right: "$$", display: true},
          {left: "\\\\[", right: "\\\\]", display: true},
          {left: "\\\\(", right: "\\\\)", display: false},
          {left: "$", right: "$", display: false}
        ],
        '''

    old_block = html[start:end]
    html = html.replace(old_block, new_delimiters)

    with open('eee-platform.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("renderMathInElement options fixed successfully!")

if __name__ == '__main__':
    main()
