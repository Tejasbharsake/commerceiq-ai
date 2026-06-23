import markdown

with open('CommerceIQ_AI_FRD.md', 'r', encoding='utf-8') as f:
    text = f.read()

html = markdown.markdown(text, extensions=['tables'])

with open('CommerceIQ_AI_FRD.html', 'w', encoding='utf-8') as f:
    f.write(html)
