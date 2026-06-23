import markdown

with open('CommerceIQ_AI_API_Spec.md', 'r', encoding='utf-8') as f:
    text = f.read()

html = markdown.markdown(text, extensions=['tables', 'fenced_code'])

with open('CommerceIQ_AI_API_Spec.html', 'w', encoding='utf-8') as f:
    f.write(html)
