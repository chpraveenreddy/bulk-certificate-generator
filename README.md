# Bulk Certificate Generator API

A FastAPI backend that generates PDF certificates in bulk for multiple recipients.

## Features

- Create certificate generation jobs
- Validate recipients individually
- Generate PDF certificates using ReportLab
- Background certificate processing
- Track job progress
- Download individual certificates
- Download all generated certificates as a ZIP
- SQLite database using SQLAlchemy
- Automated tests using pytest

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- SQLite
- ReportLab
- Pytest

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt