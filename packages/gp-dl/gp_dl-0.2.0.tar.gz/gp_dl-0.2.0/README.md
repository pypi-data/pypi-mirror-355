# Google Photos Downloader

**A Python-based Google Photos downloader built with Selenium.**

This tool automates the process of downloading photos from Google Photos albums by simulating user interaction with the web interface. It uses Selenium to open shared album links, click the "Download all" button, and extract the images to your local system.

## Features

* Accepts link-shared Google Photos album URLs
* Accepts your own Google Photos album URLs if you supply the profile directory.
* Automatically extracts downloaded `.zip` files into organized folders
* Works without needing any API keys or OAuth setup
* Supports batch downloading of multiple album links

## Why not use the Google Photos API?

**The original Google Photos API is deprecated**. While the **Google Picker API** is still available, it comes with several major limitations:

* You must select each photo manually, no "select all" option, meaning it can not be automated.
* Limited to a maximum number of items
* It requires setting up a Google Cloud project and API credentials, which is pretty hard.

## Disclaimer

* Be aware of Google’s Terms of Service before using this tool.
* It simulates human actions, but Google might not be happy about someone using this.

## Requirements

* Python 3.11+
* Selenium
* Chrome or Chromium + WebDriver (Auto-installed by Selenium if not found)

## Installation

`pip install gp-dl`

## Usage

`gp-dl --album-urls ALBUM_URL ALBUM_URL2 --output-dir test --log-level info`
