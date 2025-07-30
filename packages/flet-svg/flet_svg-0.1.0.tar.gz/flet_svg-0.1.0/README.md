# flet-svg

A [Flet](https://flet.dev/) extension to render SVG with [flutter_svg](https://pub.dev/packages/flutter_svg).

## Installation

Add dependency to `pyproject.toml` of your Flet app:

* **Git dependency**

Link to git repository:

```python
dependencies = [
  "flet-svg @ git+https://github.com/yoshoku/flet-svg",
  "flet>=0.28.3",
]
```

* **PyPi dependency**

If the package is published on pypi.org:

```python
dependencies = [
  "flet-svg",
  "flet>=0.28.3",
]
```

Build your app:

```bash
flet build <target> -v
```

## Basic Usage

Here is an example of displaying an SVG string:

```python
import flet as ft
from flet_svg import FletSvg

def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(FletSvg(
        src='<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240">'
            '<rect x="30" y="30" width="120" height="120" rx="10" fill="rgb(219, 15, 73)"/>'
            '<rect x="90" y="90" width="120" height="120" rx="10" fill="rgb(0, 141, 251)" fill-opacity="0.5"/>'
            '</svg>',
        kind='string'
    ))

ft.app(main)
```

![flet_svg example 1](https://github.com/user-attachments/assets/221aa67f-f3b2-4e54-a9e9-412adaf832d1)

Below is an example of displaying an SVG file on the network.
This SVG is the one used in the tutorial on [creating Solitaire game with Flet](https://flet.dev/docs/tutorials/python-solitaire):

```python
import flet as ft
from flet_svg import FletSvg

def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(FletSvg(
        src='https://raw.githubusercontent.com/flet-dev/'
            'examples/refs/heads/main/python/tutorials/solitaire/'
            'solitaire-game-rules/assets/images/King_clubs.svg',
        kind='network'
    ))

ft.app(main)
```

![flet_svg example 2](https://github.com/user-attachments/assets/b38000fd-2b58-4f24-8a7a-ae6655ba8202)

## Properties

flet-svg's properties correspond to the properties of [SvgPicture](https://pub.dev/documentation/flutter_svg/latest/svg/SvgPicture-class.html) class.

- `src` (str): The source of the SVG image.
- `kind` (str): The constructor to call. 'string', 'network', 'assets', 'file', or 'memory'. The default is `'string'`.
- `key` (str)
- `fit` (str): 'contain', 'fit', 'cover', 'fit_width', 'fit_height', 'none', or 'scale_down', The default is `'contain'`.
- `alignment` (str): 'center', 'bottom_right', 'bottom_center', 'bottom_left', 'top_right', 'top_center', or 'top_left'. The default is `'center'`.
- `width` (number):
- `height` (number):
- `match_text_direction` (bool): The default is `false`.
- `allow_drawing_outside_view_box` (bool):  The default is `false`.
- `semantics_label` (str):
- `exclude_from_semantics` (bool): The default is `false`.
- `clip_behavior` (str): 'hard_edge', 'none', 'anti_alias', or 'anti_alias_with_save_layer'. The default is `'hard_edge'`
