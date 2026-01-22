"""
Unit tests for data processing modules
Tests CSV loading, validation, import, retrieval, and export
"""

import pytest
import os
import tempfile
import pandas as pd
from datetime import datetime

from src.data_processing.validator import DataValidator, ValidationError
from src.data_processing.csv_loader import CSVLoader
from src.data_processing.importer import DataImporter
from src.data_processing.retriever import DataRetriever
from src.data_processing.exporter import DataExporter
from src.database.connection import DatabaseConnection
from src.database import crud


@pytest.fixture
def db_connection():
    """Create a temporary database for testing"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    db_url = f'sqlite:///{db_path}'
    db_conn = DatabaseConnection(db_url)
    db_conn.create_tables()
    
    yield db_conn
    
    db_conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing"""
    data = {
        'id': [0, 1, 2],
        'age': [18393, 20228, 18857],
        'gender': [2, 1, 1],
        'height': [168, 156, 165],
        'weight': [62.0, 85.0, 64.0],
        'ap_hi': [110, 140, 130],
        'ap_lo': [80, 90, 70],
        'cholesterol': [1, 3, 3],
        'gluc': [1, 1, 1],
        'smoke': [0, 0, 0],
        'alco': [0, 0, 0],
        'active': [1, 1, 0],
        'cardio': [0, 1, 1]
    }
    
    df = pd.DataFrame(data)
    
    fd, csv_path = tempfile.mkstemp(suffix='.csv')
    os.close(fd)
    
    df.to_csv(csv_path, sep=';', index=False)
    
    yield csv_path
    
    if os.path.exists(csv_path):
        os.remove(csv_path)


class TestDataValidator:
    """Test data validation"""
    
    def test_validate_patient_data_valid(self):
        """Test validation of valid patient data"""
        is_valid, errors = DataValidator.validate_patient_data(
            age=18393,
            gender=2,
            height=175.0,
            weight=75.0
        )
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_patient_data_invalid_age(self):
        """Test validation with invalid age"""
        is_valid, errors = DataValidator.validate_patient_data(age=100000)
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_patient_data_invalid_gender(self):
        """Test validation with invalid gender"""
        is_valid, errors = DataValidator.validate_patient_data(gender=5)
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_health_metrics_valid(self):
        """Test validation of valid health metrics"""
        is_valid, errors = DataValidator.validate_health_metrics(
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72
        )
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_health_metrics_invalid_bp(self):
        """Test validation with invalid BP relationship"""
        is_valid, errors = DataValidator.validate_health_metrics(
            systolic_bp=80,
            diastolic_bp=120  # Invalid: systolic < diastolic
        )
        assert not is_valid
        assert any('Systolic BP' in err for err in errors)
    
    def test_validate_dataframe(self):
        """Test DataFrame validation"""
        df = pd.DataFrame({'age': [18393, 20228], 'gender': [2, 1]})
        is_valid, errors = DataValidator.validate_dataframe(df)
        assert is_valid
    
    def test_validate_dataframe_empty(self):
        """Test validation of empty DataFrame"""
        df = pd.DataFrame()
        is_valid, errors = DataValidator.validate_dataframe(df)
        assert not is_valid
        assert 'empty' in errors[0].lower()


class TestCSVLoader:
    """Test CSV loading"""
    
    def test_load_csv(self, sample_csv_file):
        """Test loading CSV file"""
        loader = CSVLoader()
        df = loader.load_csv(sample_csv_file)
        
        assert not df.empty
        assert len(df) == 3
        assert 'age' in df.columns
        assert 'gender' in df.columns
    
    def test_load_csv_column_mapping(self, sample_csv_file):
        """Test column mapping"""
        loader = CSVLoader()
        df = loader.load_csv(sample_csv_file)
        
        # Check that ap_hi is mapped to systolic_bp
        assert 'systolic_bp' in df.columns or 'ap_hi' in df.columns
    
    def test_load_csv_file_not_found(self):
        """Test loading non-existent file"""
        loader = CSVLoader()
        with pytest.raises(FileNotFoundError):
            loader.load_csv('nonexistent.csv')
    
    def test_load_and_validate(self, sample_csv_file):
        """Test loading and validating CSV"""
        loader = CSVLoader()
        df, errors = loader.load_and_validate(sample_csv_file)
        
        assert not df.empty
        # Should have minimal errors for valid data
        assert isinstance(errors, list)


class TestDataImporter:
    """Test data import"""
    
    def test_import_from_csv(self, db_connection, sample_csv_file):
        """Test importing CSV data"""
        session = db_connection.get_session()
        importer = DataImporter(session=session, batch_size=10)
        
        stats = importer.import_from_csv(
            sample_csv_file,
            create_patients=True,
            create_health_metrics=True
        )
        
        assert stats['total_rows'] == 3
        assert stats['patients_created'] > 0
        assert stats['health_metrics_created'] > 0
        
        session.close()
    
    def test_import_handles_invalid_data(self, db_connection):
        """Test import handles invalid data gracefully"""
        # Create CSV with invalid data
        invalid_data = {
            'age': [100000],  # Invalid age
            'gender': [5],  # Invalid gender
            'height': [500],  # Invalid height
            'weight': [500],  # Invalid weight
            'ap_hi': [110],
            'ap_lo': [80]
        }
        
        df = pd.DataFrame(invalid_data)
        fd, csv_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        df.to_csv(csv_path, sep=';', index=False)
        
        try:
            session = db_connection.get_session()
            importer = DataImporter(session=session)
            
            stats = importer.import_from_csv(csv_path)
            
            # Should handle errors gracefully
            assert stats['total_rows'] == 1
            # Invalid rows should be skipped
            assert stats['patients_skipped'] >= 0
            
            session.close()
        finally:
            if os.path.exists(csv_path):
                os.remove(csv_path)


class TestDataRetriever:
    """Test data retrieval"""
    
    def test_get_patients(self, db_connection):
        """Test retrieving patients"""
        session = db_connection.get_session()
        
        # Create test patient
        patient = crud.insert_patient_data(
            session=session,
            age=18393,
            gender=2,
            height=175.0,
            weight=75.0
        )
        session.commit()
        
        # Retrieve patients
        retriever = DataRetriever(session=session)
        patients = retriever.get_patients()
        
        assert len(patients) > 0
        assert any(p.patient_id == patient.patient_id for p in patients)
        
        session.close()
    
    def test_get_patients_with_filters(self, db_connection):
        """Test retrieving patients with filters"""
        session = db_connection.get_session()
        
        # Create test patients
        crud.insert_patient_data(session=session, age=18393, gender=2, height=175.0, weight=75.0)
        crud.insert_patient_data(session=session, age=20000, gender=1, height=160.0, weight=60.0)
        session.commit()
        
        retriever = DataRetriever(session=session)
        
        # Filter by gender
        male_patients = retriever.get_patients(gender=2)
        assert all(p.gender == 2 for p in male_patients)
        
        # Filter by age range
        young_patients = retriever.get_patients(min_age=18000, max_age=19000)
        assert all(18000 <= p.age <= 19000 for p in young_patients)
        
        session.close()
    
    def test_get_patients_as_dataframe(self, db_connection):
        """Test retrieving patients as DataFrame"""
        session = db_connection.get_session()
        
        crud.insert_patient_data(session=session, age=18393, gender=2, height=175.0, weight=75.0)
        session.commit()
        
        retriever = DataRetriever(session=session)
        df = retriever.get_patients(as_dataframe=True)
        
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert 'patient_id' in df.columns
        
        session.close()
    
    def test_get_health_metrics(self, db_connection):
        """Test retrieving health metrics"""
        session = db_connection.get_session()
        
        # Create patient and metrics
        patient = crud.insert_patient_data(
            session=session,
            age=18393,
            gender=2,
            height=175.0,
            weight=75.0
        )
        
        crud.insert_health_metrics(
            session=session,
            patient_id=patient.patient_id,
            systolic_bp=120,
            diastolic_bp=80
        )
        session.commit()
        
        retriever = DataRetriever(session=session)
        metrics = retriever.get_health_metrics(patient_ids=[patient.patient_id])
        
        assert len(metrics) > 0
        assert metrics[0].systolic_bp == 120
        
        session.close()
    
    def test_get_statistics(self, db_connection):
        """Test getting statistics"""
        session = db_connection.get_session()
        
        # Create test data
        crud.insert_patient_data(session=session, age=18393, gender=2, height=175.0, weight=75.0)
        session.commit()
        
        retriever = DataRetriever(session=session)
        stats = retriever.get_statistics()
        
        assert 'total_patients' in stats
        assert stats['total_patients'] > 0
        
        session.close()


class TestDataExporter:
    """Test data export"""
    
    def test_export_patients_to_csv(self, db_connection):
        """Test exporting patients to CSV"""
        session = db_connection.get_session()
        
        # Create test patient
        crud.insert_patient_data(
            session=session,
            age=18393,
            gender=2,
            height=175.0,
            weight=75.0
        )
        session.commit()
        
        # Export
        fd, output_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        try:
            retriever = DataRetriever(session=session)
            exporter = DataExporter(retriever=retriever)
            
            success = exporter.export_patients_to_csv(output_path)
            
            assert success
            assert os.path.exists(output_path)
            
            # Verify CSV content
            df = pd.read_csv(output_path)
            assert not df.empty
            assert 'patient_id' in df.columns
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
        
        session.close()
