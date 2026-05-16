# SpriteFetch

<p>
	<img src="logo.svg" height="64" style="vertical-align:middle;margin-right:12px" alt="SpriteFetch logo"/>
	<span style="font-size:32px;font-weight:700;vertical-align:middle">SpriteFetch</span>
</p>

SpriteFetch is a simple Streamlit app for fetching images from a web page, converting them into SVG files, and downloading the result as a ZIP archive.

## Features

- Scan a target URL for images
- Select the assets you want to process
- Convert images to SVG
- Download the results as a ZIP file

## Run

```bash
pip install streamlit cloudscraper beautifulsoup4 pillow
streamlit run app.py
```

## Notes

Make sure the target URL is valid and that the website allows asset scraping.