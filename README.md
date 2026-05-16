<p align="center">
  <img src="logo.svg" width="96" height="96" alt="SpriteFetch logo" />
</p>

# SpriteFetch

Fetch images from web pages and convert them into SVG files.

## Table of Contents

- [Web Interface Preview](#web-interface-preview)
- [Requirements](#requirements)
- [Quickstart](#quickstart)
- [Features](#features)
- [Usage](#usage)
- [Production Readiness](#production-readiness)
- [Notes](#notes)
- [License](#license)
- [Releases](#releases)

## Web Interface Preview

Use this template to place a screenshot of the web interface in the README:

```html
<p align="center">
  <img src="docs/ui-preview.png" alt="SpriteFetch web interface preview" width="900" />
</p>
```

Replace `docs/ui-preview.png` with your actual screenshot path.

## Requirements

- Python 3.10+
- `streamlit`
- `cloudscraper`
- `beautifulsoup4`
- `Pillow`
- `requests`

Install everything with:

```bash
pip install -r requirements.txt
```

If you prefer, install only the runtime packages directly:

```bash
pip install streamlit cloudscraper beautifulsoup4 Pillow requests
```

## Quickstart

```bash
streamlit run app.py
```

## Features

- Scan a target URL for images
- Preview and select assets to convert
- Convert selected images into SVG

## Usage

1. Open the app in your browser.
2. Enter the target page URL in the `TARGET URL` field.
3. Click `SCAN TARGET`.
4. Preview the assets, select the ones you want, then click `PROCESS SELECTED`.

## Production Readiness

- **Status:** not fully production-ready yet.
- **Why:** the app is usable, but it still depends on manual validation of target sites and local file handling.
- **Recommended next steps:** add automated tests, centralized error handling, rate-limit protection, logging cleanup, and a deployment path.

## Notes

- Make sure the target URL is valid and that the website allows asset scraping.
- SVG output is stored in the `downloads/` folder.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Releases

### v0.1 — Initial release (2026-05-17)

- **Summary:** Initial public release.
- **Tag:** [v0.1](https://github.com/Pashinoh/SpriteFetch/releases/tag/v0.1)
- **Logo:** [logo.svg](logo.svg)

## Project Structure

```text
SpriteFetch/
├─ app.py
├─ logo.svg
├─ README.md
├─ requirements.txt
├─ downloads/
└─ tools/
```