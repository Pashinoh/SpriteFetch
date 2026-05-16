<p>
  <img src="logo.svg" height="96" style="vertical-align:middle;margin-right:12px" alt="SpriteFetch logo"/>
  <span style="font-size:36px;vertical-align:middle">SpriteFetch</span>
</p>

Fetch images from web pages and convert them to SVGs.

## Features

- Scan a target URL for images
- Preview and select assets to convert
- Convert images to SVG

## Run

```bash
pip install streamlit cloudscraper beautifulsoup4 pillow
streamlit run app.py
```

## Quickstart

Install runtime dependencies and run the app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Usage

- Open the app in your browser (Streamlit will display a local URL).
- Enter the target page URL in the `TARGET URL` field and click `SCAN TARGET`.
- When assets are found, preview and select the images to process.
- Click `PROCESS SELECTED` to convert chosen images to SVG and save them in the `downloads/` folder.

## Notes

Make sure the target URL is valid and that the website allows asset scraping.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Releases

### v0.1 — Initial release (2026-05-17)

- **Summary:** Initial public release. Scan a target URL for images, preview and select assets, then convert chosen images to SVG and save them to the `downloads/` folder.
- **Assets:** project logo is included at `logo.svg` (used in this README).
- **Tag:** [v0.1](https://github.com/Pashinoh/SpriteFetch/releases/tag/v0.1)

<p>
  <img src="logo.svg" height="48" alt="SpriteFetch logo" />
</p>