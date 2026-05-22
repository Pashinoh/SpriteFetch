<p align="center">
  <img src="assets/logo.svg" width="96" height="96" alt="SpriteFetch logo" />
</p>

# SpriteFetch

SpriteFetch scans web pages for images, lets you preview/select assets, and exports them in multiple formats (SVG, PNG, JPG, WEBP) for easy download and reuse.
<p>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Streamlit-1.20%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
  <img src="https://img.shields.io/badge/Cloudscraper-1.2%2B-2E86C1?style=for-the-badge" alt="Cloudscraper" />
  <img src="https://img.shields.io/badge/BeautifulSoup4-4.11%2B-6F42C1?style=for-the-badge" alt="BeautifulSoup4" />
  <img src="https://img.shields.io/badge/Pillow-9.0%2B-8E44AD?style=for-the-badge" alt="Pillow" />
  <img src="https://img.shields.io/badge/Requests-2.28%2B-28A745?style=for-the-badge" alt="Requests" />
</p>

<p align="center">
   <img src="docs/ui-preview-1.png" alt="SpriteFetch UI preview (main)" width="900" />
</p>
<table align="center">
   <tr>
      <td align="center">
         <img src="docs/ui-preview-2.png" alt="SpriteFetch UI preview (detail 1)" width="440" />
      </td>
      <td align="center">
         <img src="docs/ui-preview-3.png" alt="SpriteFetch UI preview (detail 2)" width="440" />
      </td>
   </tr>
</table>

The images above show the current UI preview for the app.

## Quickstart

Install the dependencies first, then launch the app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Local virtual environment

Create and activate a local virtual environment before installing dependencies:

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\\Scripts\\Activate.ps1
# Install dependencies inside the venv
pip install -r requirements.txt
```

Note: Do not commit the `.venv` directory to the repository. Keep it local and add it to `.gitignore` if needed.

## Features

- **Web Scraping**: Scan target URLs for all images including lazy-loaded assets
- **Asset Preview & Selection**: Interactive grid preview with bulk select/deselect options
- **Multi-Format Conversion**: Convert images to SVG, PNG, JPG, or WEBP formats
- **Batch Processing**: Convert multiple assets at once with ZIP bundling
- **Smart Filtering**: Optional keyword filtering to narrow down asset search
- **Cloudflare Bypass**: Automatic detection and bypass of Cloudflare protection

## Usage

1. **Launch the Application**:
   - Open the app in your browser after running `streamlit run app.py`

2. **Scan Target**:
   - Enter the target page URL in the `TARGET URL` field
   - Optionally, add a comma-separated keyword filter (e.g., `logo, icon, background`) to narrow down results
   - Click `SCAN TARGET` to fetch and preview all images

3. **Select Assets**:
   - Preview images in an interactive grid
   - Use the `SELECT / DESELECT ALL ASSETS` checkbox for quick bulk selection
   - Individually check/uncheck specific assets
   - Choose your desired output format (SVG, PNG, JPG, WEBP)

4. **Process & Download**:
   - Click `PROCESS SELECTED` to convert assets
   - Single images download directly
   - Multiple images are bundled into a ZIP file
   - Click `DOWNLOAD ASSET` or `DOWNLOAD .ZIP` to save

## Notes

- **Valid URLs Required**: Ensure the target URL is valid and publicly accessible
- **Scraping Compliance**: Respect website terms of service and robots.txt policies
- **Output Storage**: Downloaded files are stored in the `downloads/` folder
- **Authentication**: For protected websites, consider adding custom headers or authentication cookies if needed
- **Performance**: Large image collections may take time to process; be patient during the scanning and conversion phases

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.