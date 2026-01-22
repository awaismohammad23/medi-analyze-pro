#!/usr/bin/env python3
"""
Quick test script to verify database setup and functionality
Run this after installing dependencies to test the database module
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test if all required modules can be imported"""
    print("=" * 60)
    print("TEST 1: Testing Imports")
    print("=" * 60)
    
    try:
        from database import (
            DatabaseConnection, get_db_connection, get_session,
            Patient, HealthMetric, MedicalImage,
            BiomedicalSignal, CorrelationResult, SpectrumAnalysis,
            crud, init_database
        )
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_database_initialization():
    """Test database initialization"""
    print("\n" + "=" * 60)
    print("TEST 2: Database Initialization")
    print("=" * 60)
    
    try:
        from database import init_database, get_db_connection
        
        # Initialize database
        print("Initializing database...")
        init_database()
        print("✅ Database initialized successfully!")
        
        # Verify tables were created
        db_conn = get_db_connection()
        from sqlalchemy import inspect
        inspector = inspect(db_conn.engine)
        tables = inspector.get_table_names()
        
        expected_tables = ['patients', 'health_metrics', 'medical_images', 
                          'biomedical_signals', 'correlation_results', 'spectrum_analysis']
        
        print(f"\nCreated tables: {len(tables)}")
        for table in sorted(tables):
            status = "✅" if table in expected_tables else "⚠️"
            print(f"  {status} {table}")
        
        missing = set(expected_tables) - set(tables)
        if missing:
            print(f"\n❌ Missing tables: {missing}")
            return False
        
        print("\n✅ All expected tables created!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_crud_operations():
    """Test basic CRUD operations"""
    print("\n" + "=" * 60)
    print("TEST 3: CRUD Operations")
    print("=" * 60)
    
    try:
        from database import get_session, crud
        
        session = get_session()
        
        # Test 1: Insert Patient
        print("\n1. Testing patient insertion...")
        patient = crud.insert_patient_data(
            session=session,
            age=18393,  # ~50 years in days
            gender=2,  # Male
            height=175.0,
            weight=75.0,
            name="Test Patient"
        )
        print(f"   ✅ Patient created with ID: {patient.patient_id}")
        
        # Test 2: Retrieve Patient
        print("\n2. Testing patient retrieval...")
        patients = crud.retrieve_patient_data(session, patient_id=patient.patient_id)
        if patients and patients[0].patient_id == patient.patient_id:
            print(f"   ✅ Patient retrieved: {patients[0].name}")
        else:
            print("   ❌ Failed to retrieve patient")
            return False
        
        # Test 3: Insert Health Metrics
        print("\n3. Testing health metrics insertion...")
        metric = crud.insert_health_metrics(
            session=session,
            patient_id=patient.patient_id,
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72,
            body_temperature=36.5,
            cholesterol=1,
            glucose=1
        )
        print(f"   ✅ Health metric created with ID: {metric.metric_id}")
        
        # Test 4: Retrieve Health Metrics
        print("\n4. Testing health metrics retrieval...")
        metrics = crud.retrieve_health_metrics(session, patient_id=patient.patient_id)
        if metrics and len(metrics) > 0:
            print(f"   ✅ Retrieved {len(metrics)} health metric(s)")
        else:
            print("   ❌ Failed to retrieve health metrics")
            return False
        
        # Test 5: Update Patient
        print("\n5. Testing patient update...")
        updated = crud.update_patient_data(
            session=session,
            patient_id=patient.patient_id,
            weight=78.0
        )
        if updated and updated.weight == 78.0:
            print(f"   ✅ Patient updated: weight = {updated.weight} kg")
        else:
            print("   ❌ Failed to update patient")
            return False
        
        # Test 6: Insert Correlation Result
        print("\n6. Testing correlation result insertion...")
        correlation = crud.insert_correlation_result(
            session=session,
            metric1="systolic_bp",
            metric2="cholesterol",
            correlation_value=0.65,
            correlation_type="pearson"
        )
        print(f"   ✅ Correlation result created with ID: {correlation.correlation_id}")
        
        # Test 7: Insert Medical Image Metadata
        print("\n7. Testing medical image metadata insertion...")
        image = crud.insert_image_metadata(
            session=session,
            filename="test_xray.jpg",
            image_path="/data/images/test_xray.jpg",
            image_type="X-ray",
            patient_id=patient.patient_id
        )
        print(f"   ✅ Medical image metadata created with ID: {image.image_id}")
        
        # Test 8: Insert Biomedical Signal
        print("\n8. Testing biomedical signal insertion...")
        signal = crud.insert_biomedical_signal(
            session=session,
            signal_type="ECG",
            signal_data_path="/data/signals/ecg.csv",
            patient_id=patient.patient_id,
            sampling_rate=250.0
        )
        print(f"   ✅ Biomedical signal created with ID: {signal.signal_id}")
        
        # Test 9: Insert Spectrum Analysis
        print("\n9. Testing spectrum analysis insertion...")
        analysis = crud.insert_spectrum_analysis(
            session=session,
            signal_id=signal.signal_id,
            frequency_data_path="/data/spectrum/freq.csv",
            dominant_frequency=60.0
        )
        print(f"   ✅ Spectrum analysis created with ID: {analysis.analysis_id}")
        
        # Test 10: Delete Patient (cascade test)
        print("\n10. Testing patient deletion (cascade)...")
        deleted = crud.delete_patient_data(session, patient.patient_id)
        if deleted:
            print("   ✅ Patient deleted successfully")
            # Verify cascade delete
            remaining_metrics = crud.retrieve_health_metrics(session, patient_id=patient.patient_id)
            if len(remaining_metrics) == 0:
                print("   ✅ Cascade delete working: health metrics also deleted")
            else:
                print("   ⚠️ Cascade delete may not be working")
        else:
            print("   ❌ Failed to delete patient")
            return False
        
        session.close()
        print("\n✅ All CRUD operations successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during CRUD operations: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MediAnalyze Pro - Database Module Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Database Initialization", test_database_initialization()))
    results.append(("CRUD Operations", test_crud_operations()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Database module is working correctly.")
    else:
        print("⚠️ SOME TESTS FAILED. Please check the errors above.")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
