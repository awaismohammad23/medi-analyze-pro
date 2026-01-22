"""
Unit tests for database operations
Tests CRUD operations for all database tables
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.database.connection import DatabaseConnection
from src.database.models import (
    Patient, HealthMetric, MedicalImage, BiomedicalSignal,
    CorrelationResult, SpectrumAnalysis
)
from src.database import crud


@pytest.fixture
def db_connection():
    """Create a temporary database for testing"""
    # Create a temporary database file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Create database connection
    db_url = f'sqlite:///{db_path}'
    db_conn = DatabaseConnection(db_url)
    db_conn.create_tables()
    
    yield db_conn
    
    # Cleanup
    db_conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def session(db_connection):
    """Create a database session for testing"""
    session = db_connection.get_session()
    yield session
    session.close()


class TestPatientCRUD:
    """Test patient CRUD operations"""
    
    def test_insert_patient(self, session):
        """Test inserting a new patient"""
        patient = crud.insert_patient_data(
            session=session,
            age=18393,  # ~50 years in days
            gender=2,  # Male
            height=175.0,
            weight=75.0,
            name="Test Patient"
        )
        
        assert patient.patient_id is not None
        assert patient.name == "Test Patient"
        assert patient.age == 18393
        assert patient.gender == 2
        assert patient.height == 175.0
        assert patient.weight == 75.0
    
    def test_retrieve_patient_by_id(self, session):
        """Test retrieving patient by ID"""
        # Insert a patient
        patient = crud.insert_patient_data(
            session=session,
            age=20000,
            gender=1,
            height=160.0,
            weight=60.0
        )
        
        # Retrieve by ID
        patients = crud.retrieve_patient_data(session, patient_id=patient.patient_id)
        assert len(patients) == 1
        assert patients[0].patient_id == patient.patient_id
    
    def test_retrieve_patient_by_name(self, session):
        """Test retrieving patient by name"""
        crud.insert_patient_data(
            session=session,
            age=18000,
            gender=1,
            height=165.0,
            weight=65.0,
            name="John Doe"
        )
        
        patients = crud.retrieve_patient_data(session, name="John")
        assert len(patients) >= 1
        assert "John" in patients[0].name
    
    def test_update_patient(self, session):
        """Test updating patient data"""
        patient = crud.insert_patient_data(
            session=session,
            age=18000,
            gender=1,
            height=165.0,
            weight=65.0
        )
        
        updated = crud.update_patient_data(
            session=session,
            patient_id=patient.patient_id,
            weight=70.0,
            name="Updated Name"
        )
        
        assert updated.weight == 70.0
        assert updated.name == "Updated Name"
    
    def test_delete_patient(self, session):
        """Test deleting a patient"""
        patient = crud.insert_patient_data(
            session=session,
            age=18000,
            gender=1,
            height=165.0,
            weight=65.0
        )
        
        result = crud.delete_patient_data(session, patient.patient_id)
        assert result is True
        
        # Verify deletion
        patients = crud.retrieve_patient_data(session, patient_id=patient.patient_id)
        assert len(patients) == 0


class TestHealthMetricsCRUD:
    """Test health metrics CRUD operations"""
    
    def test_insert_health_metrics(self, session):
        """Test inserting health metrics"""
        # First create a patient
        patient = crud.insert_patient_data(
            session=session,
            age=18000,
            gender=1,
            height=165.0,
            weight=65.0
        )
        
        # Insert health metrics
        metric = crud.insert_health_metrics(
            session=session,
            patient_id=patient.patient_id,
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72,
            body_temperature=36.5,
            cholesterol=1,
            glucose=1,
            smoking=False,
            physical_activity=True
        )
        
        assert metric.metric_id is not None
        assert metric.patient_id == patient.patient_id
        assert metric.systolic_bp == 120
        assert metric.diastolic_bp == 80
        assert metric.heart_rate == 72
    
    def test_retrieve_health_metrics(self, session):
        """Test retrieving health metrics"""
        # Create patient and metrics
        patient = crud.insert_patient_data(
            session=session,
            age=18000,
            gender=1,
            height=165.0,
            weight=65.0
        )
        
        crud.insert_health_metrics(
            session=session,
            patient_id=patient.patient_id,
            systolic_bp=120,
            diastolic_bp=80
        )
        
        # Retrieve metrics
        metrics = crud.retrieve_health_metrics(session, patient_id=patient.patient_id)
        assert len(metrics) >= 1
        assert metrics[0].systolic_bp == 120


class TestMedicalImageCRUD:
    """Test medical image CRUD operations"""
    
    def test_insert_image_metadata(self, session):
        """Test inserting image metadata"""
        image = crud.insert_image_metadata(
            session=session,
            filename="test_xray.jpg",
            image_path="/path/to/test_xray.jpg",
            image_type="X-ray",
            processing_method="grayscale",
            file_size=1024000,
            width=1024,
            height=768
        )
        
        assert image.image_id is not None
        assert image.filename == "test_xray.jpg"
        assert image.image_type == "X-ray"
    
    def test_retrieve_image_metadata(self, session):
        """Test retrieving image metadata"""
        crud.insert_image_metadata(
            session=session,
            filename="test_mri.jpg",
            image_path="/path/to/test_mri.jpg",
            image_type="MRI"
        )
        
        images = crud.retrieve_image_metadata(session, image_type="MRI")
        assert len(images) >= 1
        assert images[0].image_type == "MRI"


class TestBiomedicalSignalCRUD:
    """Test biomedical signal CRUD operations"""
    
    def test_insert_biomedical_signal(self, session):
        """Test inserting biomedical signal"""
        signal = crud.insert_biomedical_signal(
            session=session,
            signal_type="ECG",
            signal_data_path="/path/to/ecg_data.csv",
            sampling_rate=250.0,
            duration=60.0,
            number_of_channels=1
        )
        
        assert signal.signal_id is not None
        assert signal.signal_type == "ECG"
        assert signal.sampling_rate == 250.0
    
    def test_retrieve_biomedical_signals(self, session):
        """Test retrieving biomedical signals"""
        crud.insert_biomedical_signal(
            session=session,
            signal_type="EEG",
            signal_data_path="/path/to/eeg_data.csv"
        )
        
        signals = crud.retrieve_biomedical_signals(session, signal_type="EEG")
        assert len(signals) >= 1
        assert signals[0].signal_type == "EEG"


class TestCorrelationResultCRUD:
    """Test correlation result CRUD operations"""
    
    def test_insert_correlation_result(self, session):
        """Test inserting correlation result"""
        result = crud.insert_correlation_result(
            session=session,
            metric1="systolic_bp",
            metric2="cholesterol",
            correlation_value=0.65,
            correlation_type="pearson",
            sample_size=1000,
            p_value=0.001
        )
        
        assert result.correlation_id is not None
        assert result.metric1 == "systolic_bp"
        assert result.metric2 == "cholesterol"
        assert result.correlation_value == 0.65
    
    def test_retrieve_correlation_results(self, session):
        """Test retrieving correlation results"""
        crud.insert_correlation_result(
            session=session,
            metric1="heart_rate",
            metric2="blood_pressure",
            correlation_value=0.45
        )
        
        results = crud.retrieve_correlation_results(session, metric1="heart_rate")
        assert len(results) >= 1
        assert results[0].metric1 == "heart_rate"


class TestSpectrumAnalysisCRUD:
    """Test spectrum analysis CRUD operations"""
    
    def test_insert_spectrum_analysis(self, session):
        """Test inserting spectrum analysis"""
        # First create a signal
        signal = crud.insert_biomedical_signal(
            session=session,
            signal_type="ECG",
            signal_data_path="/path/to/ecg.csv"
        )
        
        # Insert spectrum analysis
        analysis = crud.insert_spectrum_analysis(
            session=session,
            signal_id=signal.signal_id,
            frequency_data_path="/path/to/frequency_data.csv",
            fft_size=1024,
            frequency_resolution=0.5,
            dominant_frequency=60.0
        )
        
        assert analysis.analysis_id is not None
        assert analysis.signal_id == signal.signal_id
        assert analysis.dominant_frequency == 60.0
    
    def test_retrieve_spectrum_analyses(self, session):
        """Test retrieving spectrum analyses"""
        signal = crud.insert_biomedical_signal(
            session=session,
            signal_type="ECG",
            signal_data_path="/path/to/ecg.csv"
        )
        
        crud.insert_spectrum_analysis(
            session=session,
            signal_id=signal.signal_id,
            frequency_data_path="/path/to/freq.csv"
        )
        
        analyses = crud.retrieve_spectrum_analyses(session, signal_id=signal.signal_id)
        assert len(analyses) >= 1
        assert analyses[0].signal_id == signal.signal_id


class TestDatabaseRelationships:
    """Test database relationships and cascading"""
    
    def test_patient_health_metrics_relationship(self, session):
        """Test relationship between patient and health metrics"""
        patient = crud.insert_patient_data(
            session=session,
            age=18000,
            gender=1,
            height=165.0,
            weight=65.0
        )
        
        crud.insert_health_metrics(
            session=session,
            patient_id=patient.patient_id,
            systolic_bp=120,
            diastolic_bp=80
        )
        
        # Refresh patient to get relationships
        session.refresh(patient)
        assert len(patient.health_metrics) >= 1
    
    def test_cascade_delete(self, session):
        """Test that deleting a patient cascades to health metrics"""
        patient = crud.insert_patient_data(
            session=session,
            age=18000,
            gender=1,
            height=165.0,
            weight=65.0
        )
        
        metric = crud.insert_health_metrics(
            session=session,
            patient_id=patient.patient_id,
            systolic_bp=120,
            diastolic_bp=80
        )
        
        # Delete patient
        crud.delete_patient_data(session, patient.patient_id)
        
        # Verify health metric is also deleted (cascade)
        metrics = crud.retrieve_health_metrics(session, patient_id=patient.patient_id)
        assert len(metrics) == 0
