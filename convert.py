import sys
import subprocess

try:
    import pypandoc
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pypandoc'])
    import pypandoc

try:
    pypandoc.download_pandoc()
    pypandoc.convert_file('CommerceIQ_AI_BRD.md', 'docx', outputfile='CommerceIQ_AI_BRD.docx')
    print("Success")
except Exception as e:
    print("Error:", e)
