import re

with open("homepage_view.py", "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(r'st\.markdown\(\s*([^,\)]+),\s*unsafe_allow_html=True\s*\)', r'st.html(\1)', text)
text = text.replace('st.markdown(\n        """', 'st.html("""')

with open("homepage_view.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Successfully replaced all st.markdown with st.html in homepage_view.py")
