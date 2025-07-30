import pytest
from allyin.multimodal2text.html_cleaner import clean_html

def test_clean_html_basic():
    html = '''
    <html>
      <head><title>Sample</title></head>
      <body>
        <header>This is the header</header>
        <main>
          <h1>Main Content</h1>
          <p>This is a paragraph.</p>
        </main>
        <footer>This is the footer</footer>
      </body>
    </html>
    '''
    cleaned = clean_html(html)
    assert "Main Content" in cleaned
    assert "This is a paragraph." in cleaned
