import os, re

def strip_styles():
    for f in os.listdir('templates'):
        if f.endswith('.html'):
            path = os.path.join('templates', f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Use regex to strip out inline border and background colors that cause issues
            content = re.sub(r'style="[^"]*border-color:\s*rgba\(255,\s*255,\s*255,\s*0\.\d+\)\s*!important;?"', '', content)
            content = re.sub(r'style="[^"]*background:\s*rgba\(15,\s*23,\s*42,\s*0\.\d+\)\s*;?[^"]*"', '', content)
            content = re.sub(r'style="[^"]*border-color:\s*rgba\(255,255,255,0\.\d+\)\s*!important;?"', '', content)
            content = re.sub(r'style="[^"]*background:\s*rgba\(139,\s*92,\s*246,\s*0\.\d+\)[^"]*"', '', content)
            content = re.sub(r'style="[^"]*background:\s*rgba\(0,0,0,0\.\d+\)[^"]*"', '', content)
            
            with open(path, 'w', encoding='utf-8') as file:
                file.write(content)

if __name__ == '__main__':
    strip_styles()
    print("Done")
