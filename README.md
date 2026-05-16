<p align="center">
  <img src="assets/logo.svg" width="96" height="96" alt="SpriteFetch logo" />
</p>

# SpriteFetch

Fetch images from web pages and convert them into SVG files.
<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Streamlit-1.20%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Cloudscraper-1.2%2B-2E86C1?style=for-the-badge" alt="Cloudscraper" />
  <img src="https://img.shields.io/badge/BeautifulSoup4-4.11%2B-6F42C1?style=for-the-badge" alt="BeautifulSoup4" />
  <img src="https://img.shields.io/badge/Pillow-9.0%2B-8E44AD?style=for-the-badge" alt="Pillow" />
  <img src="https://img.shields.io/badge/Requests-2.28%2B-28A745?style=for-the-badge" alt="Requests" />
</p>

<p align="center">
  <img src="docs/ui-preview.png" alt="SpriteFetch web interface preview" width="900" />
</p>

The image above is the current UI preview for the app.

## Quickstart

Install the dependencies first, then launch the app:

```bash
pip install -r requirements.txt
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

## Notes

- Make sure the target URL is valid and that the website allows asset scraping.
- SVG output is stored in the `downloads/` folder.
- For public deployment, review scraping policy, add authentication if needed, and confirm the target environment can handle file writes.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.