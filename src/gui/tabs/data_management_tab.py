"""
Data Management Tab for MediAnalyze Pro GUI
Provides CSV loading, data viewing, and CRUD operations
"""

import sys
import os
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QTextEdit, QProgressBar, QSplitter, QHeaderView, QDialog,
    QDialogButtonBox, QFormLayout, QCheckBox, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.database import get_db_connection, get_session, crud
from src.data_processing import CSVLoader, DataImporter, DataRetriever
from ..styles import COLORS


class ImportWorker(QThread):
    """Worker thread for CSV import to prevent UI freezing"""
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(dict)  # import statistics
    error = pyqtSignal(str)  # error message
    
    def __init__(self, csv_path: str, create_patients: bool, create_metrics: bool):
        super().__init__()
        self.csv_path = csv_path
        self.create_patients = create_patients
        self.create_metrics = create_metrics
    
    def run(self):
        """Run the import in background thread"""
        try:
            session = get_session()
            importer = DataImporter(session=session, batch_size=500)
            
            # Simple progress simulation
            self.progress.emit(10, "Loading CSV file...")
            
            stats = importer.import_from_csv(
                self.csv_path,
                create_patients=self.create_patients,
                create_health_metrics=self.create_metrics
            )
            
            self.progress.emit(100, "Import completed!")
            self.finished.emit(stats)
            
        except Exception as e:
            self.error.emit(str(e))


class RetrieveWorker(QThread):
    """Worker thread for data retrieval to prevent UI freezing"""
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(object)  # pandas DataFrame
    error = pyqtSignal(str)  # error message
    
    def __init__(self, limit: int = 1000):
        super().__init__()
        self.limit = limit
        self.session = None
    
    def run(self):
        """Run the retrieval in background thread"""
        session = None
        try:
            self.progress.emit(10, "Connecting to database...")
            session = get_session()
            self.session = session
            retriever = DataRetriever(session=session)
            
            self.progress.emit(30, "Querying patient records...")
            patients_df = retriever.get_patients(limit=self.limit, as_dataframe=True)
            
            self.progress.emit(70, "Processing data...")
            
            if patients_df is None or len(patients_df) == 0:
                self.progress.emit(100, "No data found")
                self.finished.emit(None)
                return
            
            self.progress.emit(90, f"Retrieved {len(patients_df)} records")
            self.progress.emit(100, "Retrieval completed!")
            self.finished.emit(patients_df)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            # Always close the session to prevent database locks
            if session is not None:
                try:
                    session.close()
                except:
                    pass


class PatientDialog(QDialog):
    """Dialog for adding/editing patient data"""
    
    def __init__(self, parent=None, patient_data: Optional[Dict] = None):
        super().__init__(parent)
        self.patient_data = patient_data
        self.setWindowTitle("Add Patient" if patient_data is None else "Edit Patient")
        self.setMinimumWidth(400)
        self._setup_ui()
        
        if patient_data:
            self._load_patient_data()
    
    def _setup_ui(self):
        """Setup the dialog UI"""
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Apply enhanced interactive styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
            }}
            QLabel {{
                color: {COLORS['text_primary']};
                font-weight: 500;
                font-size: 11pt;
                padding: 4px 0px;
            }}
            /* Enhanced Input Fields - Interactive Design */
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                padding: 10px 14px;
                border-radius: 8px;
                font-size: 11pt;
                min-height: 20px;
            }}
            /* Hover State - Subtle highlight */
            QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {{
                border: 2px solid {COLORS['primary_light']};
                background-color: {COLORS['background']};
            }}
            /* Focus State - Active and engaging */
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border: 2px solid {COLORS['primary']};
                background-color: {COLORS['surface']};
                outline: none;
            }}
            /* ComboBox specific styling */
            QComboBox::drop-down {{
                border: none;
                width: 30px;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: {COLORS['primary']};
            }}
            QComboBox::drop-down:hover {{
                background-color: {COLORS['button_primary_hover']};
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
                width: 0;
                height: 0;
                margin-right: 8px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['surface']};
                border: 2px solid {COLORS['primary']};
                border-radius: 6px;
                selection-background-color: {COLORS['primary']};
                selection-color: white;
                padding: 4px;
            }}
            /* SpinBox buttons styling */
            QSpinBox::up-button, QDoubleSpinBox::up-button {{
                background-color: {COLORS['primary']};
                border-top-right-radius: 6px;
                width: 24px;
                height: 20px;
            }}
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
                background-color: {COLORS['button_primary_hover']};
            }}
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 5px solid white;
                width: 0;
                height: 0;
            }}
            QSpinBox::down-button, QDoubleSpinBox::down-button {{
                background-color: {COLORS['primary']};
                border-bottom-right-radius: 6px;
                width: 24px;
                height: 20px;
            }}
            QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
                background-color: {COLORS['button_primary_hover']};
            }}
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid white;
                width: 0;
                height: 0;
            }}
            /* Button styling */
            QPushButton {{
                background-color: {COLORS['button_primary']};
                color: {COLORS['button_text']};
                border: none;
                padding: 10px 24px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 11pt;
                min-width: 90px;
                min-height: 36px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['button_primary_hover']};
                transform: translateY(-1px);
            }}
            QPushButton:pressed {{
                background-color: {COLORS['button_primary_pressed']};
                transform: translateY(0px);
            }}
        """)
        
        # Name
        name_label = QLabel("Name:")
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Optional patient name")
        layout.addRow(name_label, self.name_edit)
        
        # Age (in days)
        age_label = QLabel("Age (days):")
        age_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        self.age_spin = QSpinBox()
        self.age_spin.setMinimum(0)
        self.age_spin.setMaximum(36500)  # ~100 years
        self.age_spin.setValue(10950)  # ~30 years default
        layout.addRow(age_label, self.age_spin)
        
        # Gender
        gender_label = QLabel("Gender:")
        gender_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Female", "Male"])
        layout.addRow(gender_label, self.gender_combo)
        
        # Height
        height_label = QLabel("Height:")
        height_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setMinimum(50.0)
        self.height_spin.setMaximum(250.0)
        self.height_spin.setValue(170.0)
        self.height_spin.setSuffix(" cm")
        self.height_spin.setDecimals(1)
        layout.addRow(height_label, self.height_spin)
        
        # Weight
        weight_label = QLabel("Weight:")
        weight_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-weight: 500;")
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setMinimum(20.0)
        self.weight_spin.setMaximum(300.0)
        self.weight_spin.setValue(70.0)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setDecimals(1)
        layout.addRow(weight_label, self.weight_spin)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _load_patient_data(self):
        """Load existing patient data into form"""
        if self.patient_data:
            self.name_edit.setText(self.patient_data.get('name', ''))
            self.age_spin.setValue(self.patient_data.get('age', 10950))
            self.gender_combo.setCurrentIndex(self.patient_data.get('gender', 1) - 1)
            self.height_spin.setValue(self.patient_data.get('height', 170.0))
            self.weight_spin.setValue(self.patient_data.get('weight', 70.0))
    
    def get_data(self) -> Dict:
        """Get form data as dictionary"""
        return {
            'name': self.name_edit.text().strip() or None,
            'age': self.age_spin.value(),
            'gender': self.gender_combo.currentIndex() + 1,  # 1=female, 2=male
            'height': self.height_spin.value(),
            'weight': self.weight_spin.value()
        }


class DataManagementTab(QWidget):
    """Data Management Tab - CSV loading and CRUD operations"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None  # Current DataFrame
        self.db_connection = get_db_connection()
        self.retrieve_worker = None  # Initialize worker reference
        self.import_worker = None  # Initialize import worker reference
        self._setup_ui()
        self._load_initial_data()
    
    def _setup_ui(self):
        """Setup the tab UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Top section: File operations
        file_group = self._create_file_operations_group()
        main_layout.addWidget(file_group)
        
        # Middle section: Database operations
        db_group = self._create_database_operations_group()
        main_layout.addWidget(db_group)
        
        # Bottom section: Data table
        table_group = self._create_table_group()
        main_layout.addWidget(table_group, stretch=1)
        
        # Status area
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 5px;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)
    
    def _create_file_operations_group(self) -> QGroupBox:
        """Create file operations group"""
        group = QGroupBox("CSV File Operations")
        main_layout = QVBoxLayout()
        
        # Top row: Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # Load CSV button
        self.load_csv_btn = QPushButton("📁 Load CSV File")
        self.load_csv_btn.clicked.connect(self._load_csv_file)
        button_layout.addWidget(self.load_csv_btn)
        
        # Import to database button
        self.import_btn = QPushButton("⬇️ Import to Database")
        self.import_btn.clicked.connect(self._import_to_database)
        self.import_btn.setEnabled(False)
        button_layout.addWidget(self.import_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Bottom row: File info and progress
        info_layout = QHBoxLayout()
        info_layout.setSpacing(12)
        
        # File path label
        self.file_path_label = QLabel("No file loaded")
        self.file_path_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; "
            f"padding: 8px; "
            f"background-color: {COLORS['background']}; "
            f"border-radius: 6px;"
        )
        info_layout.addWidget(self.file_path_label, stretch=1)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(28)
        self.progress_bar.setMinimumWidth(200)
        info_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(info_layout)
        group.setLayout(main_layout)
        return group
    
    def _create_database_operations_group(self) -> QGroupBox:
        """Create database operations group"""
        group = QGroupBox("Database Operations")
        main_layout = QVBoxLayout()
        
        # Button row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # CRUD buttons - clean styling using object names for stylesheet
        self.insert_btn = QPushButton("➕ Insert Patient")
        self.insert_btn.clicked.connect(self._insert_patient)
        self.insert_btn.setObjectName("successButton")
        button_layout.addWidget(self.insert_btn)
        
        self.retrieve_btn = QPushButton("🔍 Retrieve Data")
        self.retrieve_btn.clicked.connect(self._retrieve_data)
        button_layout.addWidget(self.retrieve_btn)
        
        self.update_btn = QPushButton("✏️ Update Patient")
        self.update_btn.clicked.connect(self._update_patient)
        self.update_btn.setEnabled(False)
        button_layout.addWidget(self.update_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete Patient")
        self.delete_btn.clicked.connect(self._delete_patient)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setObjectName("dangerButton")
        button_layout.addWidget(self.delete_btn)
        
        button_layout.addStretch()
        
        # Database status
        self.db_status_label = QLabel("● Connected")
        self.db_status_label.setStyleSheet(
            f"color: {COLORS['success']}; "
            f"font-weight: bold; "
            f"font-size: 12pt; "
            f"padding: 8px 12px; "
            f"background-color: {COLORS['background']}; "
            f"border-radius: 6px;"
        )
        button_layout.addWidget(self.db_status_label)
        
        main_layout.addLayout(button_layout)
        group.setLayout(main_layout)
        return group
    
    def _create_table_group(self) -> QGroupBox:
        """Create data table group"""
        group = QGroupBox("Data View")
        layout = QVBoxLayout()
        
        # Table widget
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        layout.addWidget(self.table)
        
        # Table info
        info_layout = QHBoxLayout()
        self.table_info_label = QLabel("No data loaded")
        self.table_info_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        info_layout.addWidget(self.table_info_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        group.setLayout(layout)
        return group
    
    def _load_csv_file(self):
        """Load CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            self._update_status("Loading CSV file...", "info")
            loader = CSVLoader()
            df, errors = loader.load_and_validate(file_path, strict_validation=False)
            
            if df.empty:
                QMessageBox.warning(self, "Empty File", "The CSV file is empty or contains no valid data.")
                return
            
            self.current_data = df
            self._current_csv_path = file_path  # Store path for import
            self._display_dataframe(df)
            self.file_path_label.setText(os.path.basename(file_path))
            self.import_btn.setEnabled(True)
            
            # Show validation warnings if any
            if errors:
                warning_msg = f"Loaded {len(df)} rows with {len(errors)} validation warnings.\n\nFirst 3 warnings:\n"
                for err in errors[:3]:
                    warning_msg += f"• {err}\n"
                QMessageBox.warning(self, "Validation Warnings", warning_msg)
            else:
                self._update_status(f"Successfully loaded {len(df)} rows from CSV", "success")
            
        except Exception as e:
            QMessageBox.critical(self, "Error Loading CSV", f"Failed to load CSV file:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _display_dataframe(self, df: pd.DataFrame):
        """Display DataFrame in table widget (non-blocking, chunked updates)"""
        # Limit display rows for performance (show max 1000 rows)
        display_rows = min(1000, len(df))
        
        # Set table dimensions first
        self.table.setRowCount(display_rows)
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels([str(col) for col in df.columns])
        
        # Store data for chunked population (larger chunks for faster loading)
        self._table_population_data = {
            'df': df,
            'display_rows': display_rows,
            'current_row': 0,
            'chunk_size': 200  # Process 200 rows at a time (faster)
        }
        
        # Start chunked population using QTimer
        self._populate_table_chunk()
    
    def _populate_table_chunk(self):
        """Populate table in chunks to prevent UI blocking"""
        if not hasattr(self, '_table_population_data'):
            return
        
        data = self._table_population_data
        df = data['df']
        display_rows = data['display_rows']
        start_row = data['current_row']
        chunk_size = data['chunk_size']
        end_row = min(start_row + chunk_size, display_rows)
        
        # Disable updates for this chunk
        self.table.setUpdatesEnabled(False)
        
        try:
            # Populate chunk of rows
            for i in range(start_row, end_row):
                for j, col in enumerate(df.columns):
                    value = df.iloc[i, j]
                    # Format value for display
                    if pd.isna(value):
                        display_value = ""
                    elif isinstance(value, (int, float)):
                        # Format numbers nicely
                        if isinstance(value, float):
                            display_value = f"{value:.2f}" if abs(value) < 1000 else f"{value:.0f}"
                        else:
                            display_value = str(value)
                    else:
                        display_value = str(value)
                    
                    item = QTableWidgetItem(display_value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                    self.table.setItem(i, j, item)
        finally:
            self.table.setUpdatesEnabled(True)
        
        # Update progress (less frequent updates for speed)
        data['current_row'] = end_row
        if end_row % 200 == 0 or end_row >= display_rows:  # Update every 200 rows
            progress = int((end_row / display_rows) * 100)
            self._update_status(f"Loading table: {end_row}/{display_rows} rows ({progress}%)", "info")
        
        # Process events to keep UI responsive (less frequent)
        if end_row % 200 == 0:
            QApplication.processEvents()
        
        # Continue with next chunk if not done
        if end_row < display_rows:
            # Schedule next chunk immediately (no delay for speed)
            QTimer.singleShot(1, self._populate_table_chunk)
        else:
            # Finished populating table
            self._table_population_data = None
            
            # Update info label
            if len(df) > 1000:
                self.table_info_label.setText(
                    f"Showing first 1,000 of {len(df):,} rows | {len(df.columns)} columns"
                )
            else:
                self.table_info_label.setText(f"{len(df):,} rows | {len(df.columns)} columns")
            
            self._update_status("Table loaded successfully", "success")
    
    def _import_to_database(self):
        """Import CSV data to database"""
        if self.current_data is None:
            QMessageBox.warning(self, "No Data", "Please load a CSV file first.")
            return
        
        # Ask for import options
        dialog = QDialog(self)
        dialog.setWindowTitle("Import Options")
        layout = QVBoxLayout(dialog)
        
        create_patients_check = QCheckBox("Create patient records")
        create_patients_check.setChecked(True)
        layout.addWidget(create_patients_check)
        
        create_metrics_check = QCheckBox("Create health metrics")
        create_metrics_check.setChecked(True)
        layout.addWidget(create_metrics_check)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() != QDialog.Accepted:
            return
        
        # Get file path - use current file if available, otherwise ask user
        file_path = getattr(self, '_current_csv_path', None)
        if not file_path:
            file_path = QFileDialog.getOpenFileName(
                self,
                "Select CSV File to Import",
                "",
                "CSV Files (*.csv);;All Files (*)"
            )[0]
        
        if not file_path:
            return
        
        # Start import in background thread
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.import_btn.setEnabled(False)
        self._update_status("Importing data to database...", "info")
        
        self.import_worker = ImportWorker(
            file_path,
            create_patients_check.isChecked(),
            create_metrics_check.isChecked()
        )
        self.import_worker.progress.connect(self._on_import_progress)
        self.import_worker.finished.connect(self._on_import_finished)
        self.import_worker.error.connect(self._on_import_error)
        self.import_worker.start()
    
    def _on_import_progress(self, value: int, message: str):
        """Handle import progress updates"""
        self.progress_bar.setValue(value)
        self._update_status(message, "info")
    
    def _on_import_finished(self, stats: Dict):
        """Handle import completion"""
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        
        msg = (
            f"Import completed successfully!\n\n"
            f"Total rows processed: {stats.get('total_rows', 0)}\n"
            f"Patients created: {stats.get('patients_created', 0)}\n"
            f"Health metrics created: {stats.get('metrics_created', 0)}\n"
            f"Errors: {stats.get('errors', 0)}\n"
            f"Warnings: {len(stats.get('warnings', []))}"
        )
        QMessageBox.information(self, "Import Complete", msg)
        self._update_status("Import completed successfully", "success")
        
        # Refresh data view
        self._load_initial_data()
    
    def _on_import_error(self, error_msg: str):
        """Handle import errors"""
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        QMessageBox.critical(self, "Import Error", f"Failed to import data:\n{error_msg}")
        self._update_status(f"Import failed: {error_msg}", "error")
    
    def _insert_patient(self):
        """Insert new patient"""
        dialog = PatientDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            try:
                session = get_session()
                data = dialog.get_data()
                patient = crud.insert_patient_data(
                    session,
                    age=data['age'],
                    gender=data['gender'],
                    height=data['height'],
                    weight=data['weight'],
                    name=data['name']
                )
                QMessageBox.information(
                    self,
                    "Success",
                    f"Patient created successfully!\n\nPatient ID: {patient.patient_id}"
                )
                self._update_status(f"Patient {patient.patient_id} created", "success")
                self._load_initial_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create patient:\n{str(e)}")
                self._update_status(f"Error: {str(e)}", "error")
    
    def _retrieve_data(self):
        """Retrieve data from database (runs in background thread)"""
        # Prevent multiple simultaneous retrievals
        if (hasattr(self, 'retrieve_worker') and 
            self.retrieve_worker is not None and 
            self.retrieve_worker.isRunning()):
            QMessageBox.warning(
                self,
                "Operation in Progress",
                "A data retrieval is already in progress. Please wait for it to complete."
            )
            return
        
        # Disable button during retrieval
        self.retrieve_btn.setEnabled(False)
        self._update_status("Retrieving data from database...", "info")
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Clean up any previous worker thread
        if hasattr(self, 'retrieve_worker') and self.retrieve_worker is not None:
            try:
                if self.retrieve_worker.isRunning():
                    self.retrieve_worker.terminate()
                    self.retrieve_worker.wait(1000)  # Wait up to 1 second
            except:
                pass
        
        # Start new retrieval in background thread
        self.retrieve_worker = RetrieveWorker(limit=1000)
        self.retrieve_worker.progress.connect(self._on_retrieve_progress)
        self.retrieve_worker.finished.connect(self._on_retrieve_finished)
        self.retrieve_worker.error.connect(self._on_retrieve_error)
        self.retrieve_worker.start()
    
    def _on_retrieve_progress(self, value: int, message: str):
        """Handle retrieve progress updates"""
        self.progress_bar.setValue(value)
        self._update_status(message, "info")
        
        # Process events to keep UI responsive
        QApplication.processEvents()
    
    def _on_retrieve_finished(self, patients_df):
        """Handle retrieve completion"""
        # Clean up worker thread first (non-blocking)
        if hasattr(self, 'retrieve_worker') and self.retrieve_worker is not None:
            try:
                if self.retrieve_worker.isRunning():
                    self.retrieve_worker.quit()
                    # Don't wait - let it finish in background
            except:
                pass
        
        # Process events to keep UI responsive
        QApplication.processEvents()
        
        if patients_df is None or len(patients_df) == 0:
            self.progress_bar.setVisible(False)
            self.retrieve_btn.setEnabled(True)
            QMessageBox.information(self, "No Data", "No patient records found in database.")
            self._update_status("No data found in database", "warning")
            return
        
        # Update progress bar
        self.progress_bar.setValue(100)
        self._update_status(f"Retrieved {len(patients_df)} patient records. Loading table...", "info")
        
        # Process events before heavy operation
        QApplication.processEvents()
        
        # Update UI with retrieved data (non-blocking table population)
        self.current_data = patients_df
        self._display_dataframe(patients_df)  # This now uses chunked updates
        
        # Hide progress bar after a short delay (table will show its own progress)
        QTimer.singleShot(500, lambda: self.progress_bar.setVisible(False))
        self.retrieve_btn.setEnabled(True)
    
    def _on_retrieve_error(self, error_msg: str):
        """Handle retrieve errors"""
        self.progress_bar.setVisible(False)
        self.retrieve_btn.setEnabled(True)
        
        # Clean up worker thread
        if hasattr(self, 'retrieve_worker') and self.retrieve_worker is not None:
            try:
                if self.retrieve_worker.isRunning():
                    self.retrieve_worker.quit()
                    self.retrieve_worker.wait(500)  # Wait for thread to finish
            except:
                pass
        
        QMessageBox.critical(self, "Error", f"Failed to retrieve data:\n{error_msg}")
        self._update_status(f"Error: {error_msg}", "error")
    
    def _update_patient(self):
        """Update selected patient"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a patient row to update.")
            return
        
        # Get patient ID from first column (assuming it's patient_id)
        row = selected_rows[0].row()
        patient_id_item = self.table.item(row, 0)
        
        if patient_id_item is None:
            QMessageBox.warning(self, "Invalid Selection", "Could not determine patient ID.")
            return
        
        try:
            patient_id = int(patient_id_item.text())
            session = get_session()
            patients = crud.retrieve_patient_data(session, patient_id=patient_id)
            
            if not patients:
                QMessageBox.warning(self, "Not Found", f"Patient with ID {patient_id} not found.")
                return
            
            patient = patients[0]
            patient_data = {
                'name': patient.name,
                'age': patient.age,
                'gender': patient.gender,
                'height': patient.height,
                'weight': patient.weight
            }
            
            dialog = PatientDialog(self, patient_data=patient_data)
            if dialog.exec_() == QDialog.Accepted:
                data = dialog.get_data()
                updated = crud.update_patient_data(
                    session,
                    patient_id=patient_id,
                    name=data['name'],
                    age=data['age'],
                    gender=data['gender'],
                    height=data['height'],
                    weight=data['weight']
                )
                
                if updated:
                    QMessageBox.information(self, "Success", f"Patient {patient_id} updated successfully!")
                    self._update_status(f"Patient {patient_id} updated", "success")
                    self._load_initial_data()
                else:
                    QMessageBox.warning(self, "Not Found", f"Patient {patient_id} not found.")
                    
        except ValueError:
            QMessageBox.warning(self, "Invalid ID", "Could not parse patient ID.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update patient:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _delete_patient(self):
        """Delete selected patient"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a patient row to delete.")
            return
        
        row = selected_rows[0].row()
        patient_id_item = self.table.item(row, 0)
        
        if patient_id_item is None:
            QMessageBox.warning(self, "Invalid Selection", "Could not determine patient ID.")
            return
        
        try:
            patient_id = int(patient_id_item.text())
            
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete patient {patient_id}?\n\n"
                "This will also delete all associated health metrics, images, and signals.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                session = get_session()
                deleted = crud.delete_patient_data(session, patient_id=patient_id)
                
                if deleted:
                    QMessageBox.information(self, "Success", f"Patient {patient_id} deleted successfully!")
                    self._update_status(f"Patient {patient_id} deleted", "success")
                    self._load_initial_data()
                else:
                    QMessageBox.warning(self, "Not Found", f"Patient {patient_id} not found.")
                    
        except ValueError:
            QMessageBox.warning(self, "Invalid ID", "Could not parse patient ID.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete patient:\n{str(e)}")
            self._update_status(f"Error: {str(e)}", "error")
    
    def _on_table_selection_changed(self):
        """Handle table selection changes"""
        has_selection = len(self.table.selectedItems()) > 0
        self.update_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
    
    def _load_initial_data(self):
        """Load initial data from database (non-blocking, loads minimal data)"""
        # Load initial data asynchronously to avoid blocking UI startup
        # Only load a small sample (100 rows) for initial display
        try:
            # Use a timer to load data after UI is fully rendered
            QTimer.singleShot(100, self._load_initial_data_async)
        except Exception as e:
            # Database might not be initialized yet, that's okay
            pass
    
    def _load_initial_data_async(self):
        """Load initial data asynchronously"""
        try:
            session = get_session()
            retriever = DataRetriever(session=session)
            # Load only 100 rows for initial display (faster)
            patients_df = retriever.get_patients(limit=100, as_dataframe=True)
            
            if patients_df is not None and len(patients_df) > 0:
                self.current_data = patients_df
                self._display_dataframe(patients_df)
            else:
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                self.table_info_label.setText("No data in database. Load a CSV file or insert a patient.")
        except Exception as e:
            # Database might not be initialized yet, that's okay
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            self.table_info_label.setText("No data in database. Load a CSV file or insert a patient.")
    
    def _update_status(self, message: str, status_type: str = "info"):
        """Update status label"""
        color_map = {
            "info": COLORS['text_secondary'],
            "success": COLORS['success'],
            "error": COLORS['error'],
            "warning": COLORS['warning']
        }
        color = color_map.get(status_type, COLORS['text_secondary'])
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; padding: 5px;")
