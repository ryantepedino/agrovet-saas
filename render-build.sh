#!/usr/bin/env bash
# Instala o binário Tesseract OCR e dependências do Python
apt-get update && apt-get install -y tesseract-ocr libtesseract-dev
pip install -r requirements.txt
