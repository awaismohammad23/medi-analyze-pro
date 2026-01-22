"""
CRUD operations for MediAnalyze Pro database
Provides functions for Create, Read, Update, Delete operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime
from .models import (
    Patient, HealthMetric, MedicalImage, BiomedicalSignal,
    CorrelationResult, SpectrumAnalysis
)
from .connection import get_session


# ==================== PATIENT CRUD OPERATIONS ====================

def insert_patient_data(
    session: Session,
    age: int,
    gender: int,
    height: float,
    weight: float,
    name: Optional[str] = None
) -> Patient:
    """
    Insert a new patient record
    
    Args:
        session: Database session
        age: Age in days
        gender: 1 = female, 2 = male
        height: Height in cm
        weight: Weight in kg
        name: Optional patient name
    
    Returns:
        Created Patient object
    """
    patient = Patient(
        name=name,
        age=age,
        gender=gender,
        height=height,
        weight=weight
    )
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient


def retrieve_patient_data(
    session: Session,
    patient_id: Optional[int] = None,
    name: Optional[str] = None,
    gender: Optional[int] = None,
    limit: Optional[int] = None
) -> List[Patient]:
    """
    Retrieve patient data with optional filters
    
    Args:
        session: Database session
        patient_id: Filter by patient ID
        name: Filter by name (partial match)
        gender: Filter by gender (1 = female, 2 = male)
        limit: Maximum number of results
    
    Returns:
        List of Patient objects
    """
    query = session.query(Patient)
    
    if patient_id:
        query = query.filter(Patient.patient_id == patient_id)
    if name:
        query = query.filter(Patient.name.contains(name))
    if gender:
        query = query.filter(Patient.gender == gender)
    
    query = query.order_by(desc(Patient.created_at))
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def update_patient_data(
    session: Session,
    patient_id: int,
    **kwargs
) -> Optional[Patient]:
    """
    Update patient data
    
    Args:
        session: Database session
        patient_id: Patient ID to update
        **kwargs: Fields to update (name, age, gender, height, weight)
    
    Returns:
        Updated Patient object or None if not found
    """
    patient = session.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        return None
    
    allowed_fields = ['name', 'age', 'gender', 'height', 'weight']
    for field, value in kwargs.items():
        if field in allowed_fields and value is not None:
            setattr(patient, field, value)
    
    patient.updated_at = datetime.utcnow()
    session.commit()
    session.refresh(patient)
    return patient


def delete_patient_data(session: Session, patient_id: int) -> bool:
    """
    Delete a patient record (cascades to related records)
    
    Args:
        session: Database session
        patient_id: Patient ID to delete
    
    Returns:
        True if deleted, False if not found
    """
    patient = session.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        return False
    
    session.delete(patient)
    session.commit()
    return True


# ==================== HEALTH METRICS CRUD OPERATIONS ====================

def insert_health_metrics(
    session: Session,
    patient_id: int,
    systolic_bp: Optional[int] = None,
    diastolic_bp: Optional[int] = None,
    heart_rate: Optional[int] = None,
    body_temperature: Optional[float] = None,
    oxygen_saturation: Optional[float] = None,
    cholesterol: Optional[int] = None,
    glucose: Optional[int] = None,
    smoking: Optional[bool] = None,
    alcohol_intake: Optional[bool] = None,
    physical_activity: Optional[bool] = None,
    cardiovascular_disease: Optional[bool] = None,
    timestamp: Optional[datetime] = None
) -> HealthMetric:
    """
    Insert a new health metric record
    
    Args:
        session: Database session
        patient_id: Patient ID
        systolic_bp: Systolic blood pressure
        diastolic_bp: Diastolic blood pressure
        heart_rate: Heart rate (bpm)
        body_temperature: Body temperature (°C)
        oxygen_saturation: Oxygen saturation (%)
        cholesterol: 1=normal, 2=above normal, 3=well above normal
        glucose: 1=normal, 2=above normal, 3=well above normal
        smoking: Smoking status
        alcohol_intake: Alcohol intake status
        physical_activity: Physical activity status
        cardiovascular_disease: Cardiovascular disease indicator
        timestamp: Measurement timestamp (default: now)
    
    Returns:
        Created HealthMetric object
    """
    health_metric = HealthMetric(
        patient_id=patient_id,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        heart_rate=heart_rate,
        body_temperature=body_temperature,
        oxygen_saturation=oxygen_saturation,
        cholesterol=cholesterol,
        glucose=glucose,
        smoking=smoking if smoking is not None else False,
        alcohol_intake=alcohol_intake if alcohol_intake is not None else False,
        physical_activity=physical_activity if physical_activity is not None else False,
        cardiovascular_disease=cardiovascular_disease,
        timestamp=timestamp or datetime.utcnow()
    )
    session.add(health_metric)
    session.commit()
    session.refresh(health_metric)
    return health_metric


def retrieve_health_metrics(
    session: Session,
    patient_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None
) -> List[HealthMetric]:
    """
    Retrieve health metrics with optional filters
    
    Args:
        session: Database session
        patient_id: Filter by patient ID
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of results
    
    Returns:
        List of HealthMetric objects
    """
    query = session.query(HealthMetric)
    
    if patient_id:
        query = query.filter(HealthMetric.patient_id == patient_id)
    if start_date:
        query = query.filter(HealthMetric.timestamp >= start_date)
    if end_date:
        query = query.filter(HealthMetric.timestamp <= end_date)
    
    query = query.order_by(desc(HealthMetric.timestamp))
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


# ==================== MEDICAL IMAGES CRUD OPERATIONS ====================

def insert_image_metadata(
    session: Session,
    filename: str,
    image_path: str,
    patient_id: Optional[int] = None,
    image_type: Optional[str] = None,
    processing_method: Optional[str] = None,
    file_size: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    notes: Optional[str] = None
) -> MedicalImage:
    """
    Insert medical image metadata
    
    Args:
        session: Database session
        filename: Image filename
        image_path: Path to image file
        patient_id: Optional patient ID
        image_type: Type of image (X-ray, MRI, CT scan, etc.)
        processing_method: Applied processing method
        file_size: File size in bytes
        width: Image width in pixels
        height: Image height in pixels
        notes: Additional notes
    
    Returns:
        Created MedicalImage object
    """
    medical_image = MedicalImage(
        patient_id=patient_id,
        filename=filename,
        image_path=image_path,
        image_type=image_type,
        processing_method=processing_method,
        original_filename=filename,
        file_size=file_size,
        width=width,
        height=height,
        notes=notes
    )
    session.add(medical_image)
    session.commit()
    session.refresh(medical_image)
    return medical_image


def retrieve_image_metadata(
    session: Session,
    image_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    image_type: Optional[str] = None,
    processing_method: Optional[str] = None,
    limit: Optional[int] = None
) -> List[MedicalImage]:
    """
    Retrieve medical image metadata with optional filters
    
    Args:
        session: Database session
        image_id: Filter by image ID
        patient_id: Filter by patient ID
        image_type: Filter by image type
        processing_method: Filter by processing method
        limit: Maximum number of results
    
    Returns:
        List of MedicalImage objects
    """
    query = session.query(MedicalImage)
    
    if image_id:
        query = query.filter(MedicalImage.image_id == image_id)
    if patient_id:
        query = query.filter(MedicalImage.patient_id == patient_id)
    if image_type:
        query = query.filter(MedicalImage.image_type == image_type)
    if processing_method:
        query = query.filter(MedicalImage.processing_method == processing_method)
    
    query = query.order_by(desc(MedicalImage.upload_date))
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


# ==================== BIOMEDICAL SIGNALS CRUD OPERATIONS ====================

def insert_biomedical_signal(
    session: Session,
    signal_type: str,
    signal_data_path: str,
    patient_id: Optional[int] = None,
    sampling_rate: Optional[float] = None,
    duration: Optional[float] = None,
    number_of_channels: Optional[int] = None,
    notes: Optional[str] = None
) -> BiomedicalSignal:
    """
    Insert biomedical signal metadata
    
    Args:
        session: Database session
        signal_type: Type of signal (ECG, EEG, etc.)
        signal_data_path: Path to signal data file
        patient_id: Optional patient ID
        sampling_rate: Sampling rate in Hz
        duration: Signal duration in seconds
        number_of_channels: Number of channels
        notes: Additional notes
    
    Returns:
        Created BiomedicalSignal object
    """
    signal = BiomedicalSignal(
        patient_id=patient_id,
        signal_type=signal_type,
        signal_data_path=signal_data_path,
        sampling_rate=sampling_rate,
        duration=duration,
        number_of_channels=number_of_channels,
        notes=notes
    )
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return signal


def retrieve_biomedical_signals(
    session: Session,
    signal_id: Optional[int] = None,
    patient_id: Optional[int] = None,
    signal_type: Optional[str] = None,
    limit: Optional[int] = None
) -> List[BiomedicalSignal]:
    """
    Retrieve biomedical signal metadata with optional filters
    
    Args:
        session: Database session
        signal_id: Filter by signal ID
        patient_id: Filter by patient ID
        signal_type: Filter by signal type
        limit: Maximum number of results
    
    Returns:
        List of BiomedicalSignal objects
    """
    query = session.query(BiomedicalSignal)
    
    if signal_id:
        query = query.filter(BiomedicalSignal.signal_id == signal_id)
    if patient_id:
        query = query.filter(BiomedicalSignal.patient_id == patient_id)
    if signal_type:
        query = query.filter(BiomedicalSignal.signal_type == signal_type)
    
    query = query.order_by(desc(BiomedicalSignal.timestamp))
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


# ==================== CORRELATION RESULTS CRUD OPERATIONS ====================

def insert_correlation_result(
    session: Session,
    metric1: str,
    metric2: str,
    correlation_value: float,
    correlation_type: str = 'pearson',
    sample_size: Optional[int] = None,
    p_value: Optional[float] = None,
    notes: Optional[str] = None
) -> CorrelationResult:
    """
    Insert correlation analysis result
    
    Args:
        session: Database session
        metric1: First metric name
        metric2: Second metric name
        correlation_value: Correlation coefficient
        correlation_type: 'pearson' or 'spearman'
        sample_size: Number of data points
        p_value: Statistical significance
        notes: Additional notes
    
    Returns:
        Created CorrelationResult object
    """
    result = CorrelationResult(
        metric1=metric1,
        metric2=metric2,
        correlation_value=correlation_value,
        correlation_type=correlation_type,
        sample_size=sample_size,
        p_value=p_value,
        notes=notes
    )
    session.add(result)
    session.commit()
    session.refresh(result)
    return result


def retrieve_correlation_results(
    session: Session,
    correlation_id: Optional[int] = None,
    metric1: Optional[str] = None,
    metric2: Optional[str] = None,
    limit: Optional[int] = None
) -> List[CorrelationResult]:
    """
    Retrieve correlation results with optional filters
    
    Args:
        session: Database session
        correlation_id: Filter by correlation ID
        metric1: Filter by first metric
        metric2: Filter by second metric
        limit: Maximum number of results
    
    Returns:
        List of CorrelationResult objects
    """
    query = session.query(CorrelationResult)
    
    if correlation_id:
        query = query.filter(CorrelationResult.correlation_id == correlation_id)
    if metric1:
        query = query.filter(CorrelationResult.metric1 == metric1)
    if metric2:
        query = query.filter(CorrelationResult.metric2 == metric2)
    
    query = query.order_by(desc(CorrelationResult.timestamp))
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


# ==================== SPECTRUM ANALYSIS CRUD OPERATIONS ====================

def insert_spectrum_analysis(
    session: Session,
    signal_id: int,
    frequency_data_path: str,
    fft_size: Optional[int] = None,
    frequency_resolution: Optional[float] = None,
    dominant_frequency: Optional[float] = None,
    power_spectrum_path: Optional[str] = None,
    notes: Optional[str] = None
) -> SpectrumAnalysis:
    """
    Insert spectrum analysis result
    
    Args:
        session: Database session
        signal_id: Signal ID
        frequency_data_path: Path to frequency domain data
        fft_size: FFT window size
        frequency_resolution: Frequency resolution in Hz
        dominant_frequency: Dominant frequency component
        power_spectrum_path: Path to power spectrum data
        notes: Additional notes
    
    Returns:
        Created SpectrumAnalysis object
    """
    analysis = SpectrumAnalysis(
        signal_id=signal_id,
        frequency_data_path=frequency_data_path,
        fft_size=fft_size,
        frequency_resolution=frequency_resolution,
        dominant_frequency=dominant_frequency,
        power_spectrum_path=power_spectrum_path,
        notes=notes
    )
    session.add(analysis)
    session.commit()
    session.refresh(analysis)
    return analysis


def retrieve_spectrum_analyses(
    session: Session,
    analysis_id: Optional[int] = None,
    signal_id: Optional[int] = None,
    limit: Optional[int] = None
) -> List[SpectrumAnalysis]:
    """
    Retrieve spectrum analysis results with optional filters
    
    Args:
        session: Database session
        analysis_id: Filter by analysis ID
        signal_id: Filter by signal ID
        limit: Maximum number of results
    
    Returns:
        List of SpectrumAnalysis objects
    """
    query = session.query(SpectrumAnalysis)
    
    if analysis_id:
        query = query.filter(SpectrumAnalysis.analysis_id == analysis_id)
    if signal_id:
        query = query.filter(SpectrumAnalysis.signal_id == signal_id)
    
    query = query.order_by(desc(SpectrumAnalysis.timestamp))
    
    if limit:
        query = query.limit(limit)
    
    return query.all()
