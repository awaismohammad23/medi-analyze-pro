# MediAnalyze Pro

A comprehensive healthcare data and medical image processing application for managing patient health data, analyzing biomedical signals, processing medical images, and creating interactive visualizations.

## Overview

MediAnalyze Pro is a desktop application built with PyQt5 that provides healthcare professionals and researchers with tools to:
- Manage and analyze patient health metrics
- Process and analyze biomedical signals (ECG/EEG)
- Process medical images (X-ray, MRI, CT scans)
- Generate comprehensive data visualizations
- Perform statistical analysis and correlation studies

## Features

### ✅ Implemented Features

**Phase 1-2: Foundation & Database**
- Project structure and setup
- SQLite database with 6 tables (patients, health_metrics, medical_images, biomedical_signals, correlation_results, spectrum_analysis)
- Complete CRUD operations with relationships

**Phase 3-4: Data Management**
- CSV data loading with auto-delimiter detection
- Data validation (medical value ranges, data types)
- Bulk data import with progress tracking
- Flexible data retrieval with filtering
- Data export to CSV

**Phase 5: Signal Processing**
- Synthetic ECG/EEG signal generation
- Signal loading from CSV/TXT/DAT files
- Signal preprocessing (normalization, filtering, noise reduction)
- FFT spectrum analysis (magnitude, power spectrum, PSD)

**Phase 6: Image Processing**
- Medical image loading (PNG, JPEG, BMP, TIFF, DICOM)
- Image processing operations (grayscale, blur, edge detection, thresholding, CLAHE)
- Image metadata extraction and database storage

**Phase 7: Visualization**
- Time-series plots
- Scatter plots with correlation analysis
- Correlation heatmaps
- FFT spectrum plots
- Image comparison viewer

**Phase 8-13: GUI Application**
- **Data Management Tab**: CSV import, patient CRUD operations, data retrieval
- **Health Analysis Tab**: Data filtering, correlation analysis (Pearson/Spearman), time-series analysis
- **Spectrum Analysis Tab**: Signal loading, synthetic generation, FFT analysis with multiple visualizations
- **Image Processing Tab**: Image upload, processing operations, side-by-side comparison
- **Data Visualization Tab**: Comprehensive visualization interface for all data types

## Technology Stack

- **Language**: Python 3.8+
- **GUI**: PyQt5
- **Database**: SQLite (SQLAlchemy ORM)
- **Data Processing**: NumPy, Pandas, SciPy
- **Image Processing**: OpenCV, Pillow
- **Visualization**: Matplotlib, Seaborn

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd "MediAnalyze Pro"
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # OR
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Launch GUI Application
```bash
python run_gui.py
```

### Run Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_database.py

# Run with coverage
pytest --cov=src tests/
```

### Initialize Database
```bash
python -m src.database.init_db
```

## Project Structure

```
MediAnalyze Pro/
├── src/
│   ├── database/          # Database models, CRUD operations
│   ├── data_processing/   # Data loading, filtering, correlation
│   ├── signal_processing/ # FFT analysis, signal generation
│   ├── image_processing/  # Image operations, metadata
│   ├── visualization/    # Plotting functions
│   └── gui/               # PyQt5 GUI components
│       └── tabs/          # Feature tabs (5 tabs implemented)
├── data/                  # Data storage (images, signals, processed data)
├── tests/                 # Unit and integration tests
├── datasets/              # Sample datasets
├── run_gui.py             # Application entry point
└── requirements.txt       # Python dependencies
```

## Usage

### Data Management
1. Use **Data Management** tab to import CSV files with health data
2. View, insert, update, or delete patient records
3. Retrieve and filter data from the database

### Health Analysis
1. Load health metrics from database
2. Apply filters (Moving Average, Threshold, Outlier Removal)
3. Compute correlations between metrics (Pearson/Spearman)
4. Generate time-series visualizations

### Spectrum Analysis
1. Load signal files or generate synthetic ECG/EEG signals
2. Configure FFT parameters (window function, frequency range)
3. View time-domain, frequency-domain, and power spectrum plots

### Image Processing
1. Upload medical images (X-ray, MRI, CT)
2. Apply processing operations (blur, edge detection, thresholding, etc.)
3. Compare original vs processed images side-by-side
4. View image metadata

### Data Visualization
1. Select visualization type (Time-Series, Scatter, Heatmap, FFT, Image Comparison)
2. Load data from database, CSV, signal files, or images
3. Configure visualization parameters
4. Generate and export visualizations

## Testing

Comprehensive unit tests are available for all modules:
- Database operations
- Data processing (loading, filtering, correlation)
- Signal processing
- Image processing
- Visualization
- GUI components

Run tests with: `pytest`

## Development Status

**Current Phase**: Phase 13 Complete ✅

All core features have been implemented and tested. The application is fully functional with a professional GUI interface.

## License

*License information to be added*

---

**Last Updated**: Phase 13 - Data Visualization Tab Complete
