# 🛒 Advanced POS Management System (نظام المبيعات المتكامل)

A modern, fast, and cross-platform Point of Sale application built with Python and CustomTkinter.

## Features
- 💸 **Sales Management**: Quick barcode scanning and cart system.
- 📦 **Inventory Tracking**: Manage products, stock levels, and low-stock alerts.
- 📊 **Analytics**: Detailed yearly revenue and profit charts (Bar/Line).
- 💳 **Credit System**: Track customer debts and payment history.
- 🌍 **Multilingual**: Supports Arabic, English, and French.
- 🎨 **Modern UI**: Dark/Light mode with dynamic accent colors.

## Running on Linux
```bash
python3 main.py
```

## Running on Windows
```bash
python main.py
```

## Build Executable (.exe)
```bash
pyinstaller --onefile --windowed --name="POS_System" main.py
```

## Directory Structure
```
pos_system/
├── main.py          ← Entry point & navigation
├── database.py      ← SQLite database logic
├── theme.py         ← UI Styles & Icons
├── ui_products.py   ← Product Management
├── ui_sales.py      ← POS & Barcode scanning
├── ui_analytics.py  ← Charts & Reports
├── ui_settings.py   ← App Configuration
└── data.db          ← Database file (auto-generated)
```

## Prerequisites
```bash
pip install customtkinter matplotlib reportlab arabic-reshaper python-bidi pillow
```
