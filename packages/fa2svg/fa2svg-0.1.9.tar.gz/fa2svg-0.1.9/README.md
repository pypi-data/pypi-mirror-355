# fa2svg

A small Python package that converts Font Awesome `<i>`/`<span>` tags into email‑friendly inline images. You can embed either raw SVG (`to_inline_svg`) or high‑density PNG (`to_inline_png_img`), preserving font‑size, color, aspect ratio, and baseline alignment. Includes a simple test script at `tests/run_test.py` to verify basic functionality.

---

## Installation

```bash
pip install fa2svg
```

Or for local development:

```bash
git clone https://github.com/meena-erian/fa2svg.git
cd fa2svg
pip install -e .
```

---

## Upload to PyPI

Ensure your `.pypirc` is configured, then:

```bash
# from project root
env/bin/python -m build
twine upload --config-file "./.pypirc" dist/*
```

---

## Usage

```python
from fa2svg.converter import to_inline_svg, to_inline_png_img

html = '''
  <p>
    Coffee time:
    <i class="fas fa-mug-saucer" style="font-size:64px;color:#c60"></i>
    and stars:
    <span class="far fa-star" style="font-size:48px;color:gold"></span>
  </p>
'''

# Embed as SVG data URI:
converted_svg = to_inline_svg(html)

# Embed as higher-resolution PNG data URI:
converted_png = to_inline_png_img(html)

print(converted_svg)
print(converted_png)
```

---

## API

* **`to_inline_svg(html: str) -> str`**
  
  Fetches the correct FA SVG, inlines your `font-size` and `color`, and outputs an `<img>` tag with a base64‑encoded SVG data URI, plus `width`, `height`, and `vertical-align` CSS.

* **`to_inline_png_img(html: str) -> str`**
  
  Same as above but renders a PNG at higher pixel density (default 2×) for crisper images in clients with varying DPI.

---

## Testing

A basic test harness is provided at `tests/run_test.py`:

```bash
python -m tests.run_test
```

---

## Contributing

1. Fork the repo
2. Create a feature branch
3. Commit & push your changes
4. Open a Pull Request

Issues and PRs are very welcome!
