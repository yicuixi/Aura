# SearXNG Search Integration

This directory contains Docker deployment files and configuration for the SearXNG search engine, providing web search capabilities for Aura.

## Files

- `docker-compose.yml`: Docker Compose configuration file
- `settings/settings.yml`: SearXNG configuration file
- `start_searxng.bat`: Quick start batch script for SearXNG
- `test_search.py`: Python script to test search functionality

## Usage

1. **Start SearXNG**:
   - Double-click `start_searxng.bat`
   - Or run `docker-compose up -d` in this directory

2. **Test Search Functionality**:
   - Run `python test_search.py` in this directory
   - This will test if Aura's tool search function works properly

3. **Access SearXNG Web Interface**:
   - Open http://localhost:8088 in your browser

## Troubleshooting

- If search doesn't work, make sure:
  1. SearXNG container is running (check with `docker ps`)
  2. You can access http://localhost:8088 in browser
  3. Port 8088 is not used by another program

- To change the port, edit port mapping in `docker-compose.yml` (e.g., to `"8089:8080"`) and update the URL in `tools.py`.

## Notes

1. This is a local deployment for development use
2. For production, additional security configurations are recommended
3. Default configuration enables Google, Bing, DuckDuckGo, and Wikipedia as search sources
