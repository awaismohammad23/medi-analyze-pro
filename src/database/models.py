"""
Database models/schema for MediAnalyze Pro
Defines all database tables and their relationships
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Patient(Base):
    """Patients table - stores basic patient information"""
    __tablename__ = 'patients'
    
    patient_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)  # Optional name field
    age = Column(Integer, nullable=False)  # Age in days (as per dataset format)
    gender = Column(Integer, nullable=False)  # 1 = female, 2 = male
    height = Column(Float, nullable=False)  # Height in cm
    weight = Column(Float, nullable=False)  # Weight in kg
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    health_metrics = relationship("HealthMetric", back_populates="patient", cascade="all, delete-orphan")
    medical_images = relationship("MedicalImage", back_populates="patient", cascade="all, delete-orphan")
    biomedical_signals = relationship("BiomedicalSignal", back_populates="patient", cascade="all, delete-orphan")


class HealthMetric(Base):
    """Health metrics table - stores patient health measurements over time"""
    __tablename__ = 'health_metrics'
    
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Health measurements
    systolic_bp = Column(Integer, nullable=True)  # ap_hi - systolic blood pressure
    diastolic_bp = Column(Integer, nullable=True)  # ap_lo - diastolic blood pressure
    heart_rate = Column(Integer, nullable=True)  # Heart rate (bpm)
    body_temperature = Column(Float, nullable=True)  # Body temperature (°C)
    oxygen_saturation = Column(Float, nullable=True)  # SpO2 (%)
    cholesterol = Column(Integer, nullable=True)  # 1: normal, 2: above normal, 3: well above normal
    glucose = Column(Integer, nullable=True)  # 1: normal, 2: above normal, 3: well above normal
    
    # Lifestyle factors
    smoking = Column(Boolean, default=False)  # smoke
    alcohol_intake = Column(Boolean, default=False)  # alco
    physical_activity = Column(Boolean, default=False)  # active
    
    # Cardiovascular disease indicator
    cardiovascular_disease = Column(Boolean, nullable=True)  # cardio
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    patient = relationship("Patient", back_populates="health_metrics")


class MedicalImage(Base):
    """Medical images table - stores metadata for medical images"""
    __tablename__ = 'medical_images'
    
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=True)  # Optional - can be standalone
    filename = Column(String(255), nullable=False)
    image_path = Column(String(500), nullable=False)  # Path to the image file
    image_type = Column(String(50), nullable=True)  # X-ray, MRI, CT scan, etc.
    processing_method = Column(String(100), nullable=True)  # grayscale, edge_detection, etc.
    original_filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    width = Column(Integer, nullable=True)  # Image width in pixels
    height = Column(Integer, nullable=True)  # Image height in pixels
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)  # Additional notes or metadata
    
    # Relationship
    patient = relationship("Patient", back_populates="medical_images")


class BiomedicalSignal(Base):
    """Biomedical signals table - stores metadata for ECG/EEG signals"""
    __tablename__ = 'biomedical_signals'
    
    signal_id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=True)  # Optional
    signal_type = Column(String(50), nullable=False)  # ECG, EEG, etc.
    signal_data_path = Column(String(500), nullable=False)  # Path to signal data file
    sampling_rate = Column(Float, nullable=True)  # Sampling rate in Hz
    duration = Column(Float, nullable=True)  # Signal duration in seconds
    number_of_channels = Column(Integer, nullable=True)  # Number of channels
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)  # Additional notes
    
    # Relationship
    patient = relationship("Patient", back_populates="biomedical_signals")
    spectrum_analyses = relationship("SpectrumAnalysis", back_populates="signal", cascade="all, delete-orphan")


class CorrelationResult(Base):
    """Correlation results table - stores computed correlation coefficients"""
    __tablename__ = 'correlation_results'
    
    correlation_id = Column(Integer, primary_key=True, autoincrement=True)
    metric1 = Column(String(100), nullable=False)  # First metric name (e.g., 'systolic_bp')
    metric2 = Column(String(100), nullable=False)  # Second metric name (e.g., 'cholesterol')
    correlation_value = Column(Float, nullable=False)  # Pearson or Spearman correlation coefficient
    correlation_type = Column(String(20), nullable=False, default='pearson')  # 'pearson' or 'spearman'
    sample_size = Column(Integer, nullable=True)  # Number of data points used
    p_value = Column(Float, nullable=True)  # Statistical significance
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)  # Additional notes


class SpectrumAnalysis(Base):
    """Spectrum analysis table - stores FFT analysis results"""
    __tablename__ = 'spectrum_analysis'
    
    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(Integer, ForeignKey('biomedical_signals.signal_id'), nullable=False)
    frequency_data_path = Column(String(500), nullable=False)  # Path to frequency domain data
    fft_size = Column(Integer, nullable=True)  # FFT window size
    frequency_resolution = Column(Float, nullable=True)  # Frequency resolution in Hz
    dominant_frequency = Column(Float, nullable=True)  # Dominant frequency component
    power_spectrum_path = Column(String(500), nullable=True)  # Path to power spectrum data
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)  # Additional notes
    
    # Relationship
    signal = relationship("BiomedicalSignal", back_populates="spectrum_analyses")
