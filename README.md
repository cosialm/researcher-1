# Researcher-1

This script uses Playwright to automate a search on Bohrium AI, extracts the results, and saves them to a `.docx` file.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/researcher-1.git
    cd researcher-1
    ```
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Install the Playwright browsers:
    ```bash
    playwright install
    ```

## Usage

To run the script, use the following command:

```bash
python researcher-1.py "Your search prompt"
```

For example:

```bash
python researcher-1.py "The impact of AI in education"
```

You can also run the script in headless mode (without opening a browser window) by using the `--headless` flag:

```bash
python researcher-1.py "Your search prompt" --headless
```

The script will create a `.docx` file in the same directory with the search results. The filename will be in the format `bohrium_ai_response_YYYYMMDD_HHMMSS_UUID.docx`.