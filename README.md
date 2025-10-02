# HA Chile Water Price – Backend Processor

This repository provides the complete backend pipeline for the **Home Assistant custom integration: HA Chile Water Price**, which tracks and exposes the official water pricing information for different regions, companies, and locations in Chile.

The backend is responsible for scraping, downloading, parsing, and structuring water tariff data published by the **Superintendencia de Servicios Sanitarios (SISS)**.

---

## 🧠 What This Does

The pipeline performs the following steps:

1. **Scrapes the official SISS tariff page** to detect updates.
2. **Hashes the page content** and checks for changes using the `Last-Modified` header and content checksum.
3. **Downloads updated PDF files** containing water pricing regulations.
4. **Parses the new PDFs** using heuristics to extract key information from variable PDF layouts.
5. **Generates structured JSON files** with sectioned data:
   - General information
   - Fixed charges
   - Variable tariffs (potable water, wastewater, etc.)
   - Special charges (cut, reconnection, RILES, etc.)
6. **Outputs all processed data to a standardized directory**, ready to be used by the Home Assistant integration.

---

## 🏗️ Folder Structure

```text
📁 /data
    └── json/                 # Output structured JSON files
    └── pdf/                  # Downloaded PDFs
    └── meta/                 # SHA hashes, headers, and state files
📁 /scripts
    ├── scraper.py           # Detects updates on the SISS website
    ├── download_pdfs.py     # Downloads updated PDF files
    ├── parse_pdfs.py        # Parses PDF files into structured JSON
    ├── main.py              # Orchestrates the pipeline
📄 requirements.txt
📄 Dockerfile
📄 docker-compose.yml```

## 🐳 Docker Setup

### Build and Run with Docker Compose

```bash
docker compose up --build
```

The container will automatically:

1. Run `scraper.py` to check for changes.
2. If changes are detected, run `download_pdfs.py`.
3. If new PDFs were downloaded, run `parse_pdfs.py`.

---

## ⏰ Cron Job (Inside Container)

To automate the process at 3:00 AM on Sundays and Wednesdays, add this to the container’s crontab:

```cron
0 3 * * 0,3 python3 /app/scripts/scraper.py >> /var/log/cron.log 2>&1
```

Make sure your Dockerfile sets up the cron daemon and keeps the container alive.

---

## 📄 Requirements

All dependencies are listed in `requirements.txt`:

```text
pdfplumber==0.10.3  
PyPDF2==3.0.1  
pandas==2.2.2  
python-dateutil==2.9.0.post0  
requests==2.31.0  
beautifulsoup4==4.12.3  
lxml==5.2.1
```

---

## 🔧 Future Integration

This backend will power a Home Assistant integration that:

- Automatically detects your region, company, and locality.
- Creates entities with your current water prices.
- Provides update notifications when tariffs change.
- Supports automations and dashboards.

---

## 👨‍💻 Author

Developed by Edison Montes [@_GeekMD_](https://github.com/Geek-MD)  
Open-source and proudly built in 🇨🇱
