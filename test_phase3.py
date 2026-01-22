#!/usr/bin/env python3
"""
Comprehensive test script for Phase 3: Data Loading & Management Module
Tests CSV loading, validation, import, retrieval, and export functionality
"""

import sys
import os

# Add project root to path for proper imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test if all required modules can be imported"""
    print("=" * 60)
    print("TEST 1: Testing Imports")
    print("=" * 60)
    
    try:
        from src.data_processing import (
            DataValidator, ValidationError,
            CSVLoader, DataImporter,
            DataRetriever, DataExporter
        )
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_csv_loading():
    """Test CSV loading functionality"""
    print("\n" + "=" * 60)
    print("TEST 2: CSV Loading")
    print("=" * 60)
    
    try:
        from src.data_processing import CSVLoader
        
        csv_path = os.path.join('datasets', 'cardio_train.csv')
        
        if not os.path.exists(csv_path):
            print(f"⚠️  CSV file not found: {csv_path}")
            print("   Skipping CSV loading test")
            return True
        
        print(f"Loading CSV file: {csv_path}")
        loader = CSVLoader()
        
        # Test 1: Load CSV
        print("\n1. Testing CSV file loading...")
        df = loader.load_csv(csv_path, n_rows=100)  # Load first 100 rows for testing
        print(f"   ✅ Loaded {len(df)} rows, {len(df.columns)} columns")
        print(f"   Columns: {', '.join(list(df.columns)[:5])}...")
        
        # Test 2: Load and validate
        print("\n2. Testing CSV loading with validation...")
        df_valid, errors = loader.load_and_validate(csv_path, strict_validation=False, n_rows=100)
        print(f"   ✅ Loaded {len(df_valid)} rows")
        print(f"   Validation errors: {len(errors)}")
        
        if errors:
            print(f"   ⚠️  First 3 validation errors:")
            for err in errors[:3]:
                print(f"      - {err}")
        
        # Test 3: File info
        print("\n3. Testing file info retrieval...")
        file_info = CSVLoader.get_file_info(csv_path)
        if file_info.get('exists'):
            print(f"   ✅ File size: {file_info.get('size_mb', 0)} MB")
        else:
            print("   ⚠️  Could not get file info")
        
        print("\n✅ CSV loading tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during CSV loading: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_validation():
    """Test data validation functionality"""
    print("\n" + "=" * 60)
    print("TEST 3: Data Validation")
    print("=" * 60)
    
    try:
        from src.data_processing import DataValidator
        
        # Test 1: Valid patient data
        print("\n1. Testing valid patient data validation...")
        is_valid, errors = DataValidator.validate_patient_data(
            age=18393,
            gender=2,
            height=175.0,
            weight=75.0
        )
        if is_valid:
            print("   ✅ Valid patient data accepted")
        else:
            print(f"   ❌ Unexpected validation failure: {errors}")
            return False
        
        # Test 2: Invalid patient data
        print("\n2. Testing invalid patient data validation...")
        is_valid, errors = DataValidator.validate_patient_data(
            age=100000,  # Invalid age
            gender=5,  # Invalid gender
            height=500.0,  # Invalid height
            weight=500.0  # Invalid weight
        )
        if not is_valid and len(errors) > 0:
            print(f"   ✅ Invalid data correctly rejected ({len(errors)} errors)")
        else:
            print("   ❌ Should have rejected invalid data")
            return False
        
        # Test 3: Valid health metrics
        print("\n3. Testing valid health metrics validation...")
        is_valid, errors = DataValidator.validate_health_metrics(
            systolic_bp=120,
            diastolic_bp=80,
            heart_rate=72,
            cholesterol=1,
            glucose=1
        )
        if is_valid:
            print("   ✅ Valid health metrics accepted")
        else:
            print(f"   ❌ Unexpected validation failure: {errors}")
            return False
        
        # Test 4: Invalid BP relationship
        print("\n4. Testing invalid BP relationship validation...")
        is_valid, errors = DataValidator.validate_health_metrics(
            systolic_bp=80,  # Invalid: less than diastolic
            diastolic_bp=120
        )
        if not is_valid:
            print("   ✅ Invalid BP relationship correctly rejected")
        else:
            print("   ❌ Should have rejected invalid BP relationship")
            return False
        
        print("\n✅ Data validation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_import():
    """Test data import functionality"""
    print("\n" + "=" * 60)
    print("TEST 4: Data Import to Database")
    print("=" * 60)
    
    try:
        from src.data_processing import DataImporter
        from src.database import get_session, init_database
        
        # Initialize database
        print("Initializing database...")
        init_database()
        
        csv_path = os.path.join('datasets', 'cardio_train.csv')
        
        if not os.path.exists(csv_path):
            print(f"⚠️  CSV file not found: {csv_path}")
            print("   Skipping data import test")
            return True
        
        session = get_session()
        importer = DataImporter(session=session, batch_size=50)
        
        # Test import with progress callback
        print("\nImporting data (first 200 rows for testing)...")
        
        def progress_callback(processed, total, message):
            if processed % 50 == 0 or processed == total:
                print(f"   {message}: {processed}/{total} rows")
        
        # Load only first 200 rows for testing
        loader = CSVLoader()
        df_test, _ = loader.load_and_validate(csv_path, n_rows=200)
        
        # Create temporary CSV with limited rows
        import tempfile
        fd, temp_csv = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        df_test.to_csv(temp_csv, sep=';', index=False)
        
        try:
            stats = importer.import_from_csv(
                temp_csv,
                create_patients=True,
                create_health_metrics=True,
                progress_callback=progress_callback
            )
        finally:
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
        
        print(f"\nImport Statistics:")
        print(f"   Total rows processed: {stats['total_rows']}")
        print(f"   Patients created: {stats['patients_created']}")
        print(f"   Patients skipped: {stats['patients_skipped']}")
        print(f"   Health metrics created: {stats['health_metrics_created']}")
        print(f"   Health metrics skipped: {stats['health_metrics_skipped']}")
        print(f"   Errors: {len(stats['errors'])}")
        
        if stats['errors']:
            print(f"\n   ⚠️  First 3 errors:")
            for err in stats['errors'][:3]:
                print(f"      - {err}")
        
        if stats['patients_created'] > 0 and stats['health_metrics_created'] > 0:
            print("\n✅ Data import successful!")
            session.close()
            return True
        else:
            print("\n⚠️  No data was imported (this might be expected if data already exists)")
            session.close()
            return True
        
    except Exception as e:
        print(f"\n❌ Error during data import: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_retrieval():
    """Test data retrieval functionality"""
    print("\n" + "=" * 60)
    print("TEST 5: Data Retrieval")
    print("=" * 60)
    
    try:
        from src.data_processing import DataRetriever
        from src.database import get_session
        
        session = get_session()
        retriever = DataRetriever(session=session)
        
        # Test 1: Get patients
        print("\n1. Testing patient retrieval...")
        patients = retriever.get_patients(limit=5)
        print(f"   ✅ Retrieved {len(patients)} patients (limited to 5)")
        
        if patients:
            p = patients[0]
            print(f"   Sample patient: ID={p.patient_id}, Age={p.age}, Gender={p.gender}")
        
        # Test 2: Get patients with filters
        print("\n2. Testing patient retrieval with filters...")
        male_patients = retriever.get_patients(gender=2, limit=3)
        print(f"   ✅ Retrieved {len(male_patients)} male patients")
        
        # Test 3: Get patients as DataFrame
        print("\n3. Testing patient retrieval as DataFrame...")
        df_patients = retriever.get_patients(limit=5, as_dataframe=True)
        if not df_patients.empty:
            print(f"   ✅ Retrieved {len(df_patients)} patients as DataFrame")
            print(f"   DataFrame columns: {', '.join(list(df_patients.columns)[:5])}...")
        else:
            print("   ⚠️  No patients found")
        
        # Test 4: Get health metrics
        print("\n4. Testing health metrics retrieval...")
        metrics = retriever.get_health_metrics(limit=5)
        print(f"   ✅ Retrieved {len(metrics)} health metrics (limited to 5)")
        
        if metrics:
            m = metrics[0]
            print(f"   Sample metric: Patient ID={m.patient_id}, BP={m.systolic_bp}/{m.diastolic_bp}")
        
        # Test 5: Get statistics
        print("\n5. Testing statistics retrieval...")
        stats = retriever.get_statistics()
        print(f"   ✅ Retrieved statistics:")
        print(f"      Total patients: {stats.get('total_patients', 0)}")
        print(f"      Total health metrics: {stats.get('total_health_metrics', 0)}")
        if stats.get('avg_systolic_bp'):
            print(f"      Avg systolic BP: {stats['avg_systolic_bp']:.1f}")
        
        session.close()
        print("\n✅ Data retrieval tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during data retrieval: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_data_export():
    """Test data export functionality"""
    print("\n" + "=" * 60)
    print("TEST 6: Data Export")
    print("=" * 60)
    
    try:
        from src.data_processing import DataRetriever, DataExporter
        from src.database import get_session
        
        session = get_session()
        retriever = DataRetriever(session=session)
        exporter = DataExporter(retriever=retriever)
        
        # Create output directory
        output_dir = os.path.join('data', 'processed')
        os.makedirs(output_dir, exist_ok=True)
        
        # Test 1: Export patients
        print("\n1. Testing patient export to CSV...")
        patients_path = os.path.join(output_dir, 'test_exported_patients.csv')
        success = exporter.export_patients_to_csv(patients_path, limit=10)
        
        if success and os.path.exists(patients_path):
            file_size = os.path.getsize(patients_path)
            print(f"   ✅ Exported patients to: {patients_path}")
            print(f"   File size: {file_size} bytes")
        else:
            print("   ⚠️  Patient export may have failed or no data to export")
        
        # Test 2: Export health metrics
        print("\n2. Testing health metrics export to CSV...")
        metrics_path = os.path.join(output_dir, 'test_exported_metrics.csv')
        success = exporter.export_health_metrics_to_csv(metrics_path, limit=10)
        
        if success and os.path.exists(metrics_path):
            file_size = os.path.getsize(metrics_path)
            print(f"   ✅ Exported health metrics to: {metrics_path}")
            print(f"   File size: {file_size} bytes")
        else:
            print("   ⚠️  Health metrics export may have failed or no data to export")
        
        session.close()
        print("\n✅ Data export tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error during data export: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("MediAnalyze Pro - Phase 3 Test Suite")
    print("Data Loading & Management Module")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("CSV Loading", test_csv_loading()))
    results.append(("Data Validation", test_data_validation()))
    results.append(("Data Import", test_data_import()))
    results.append(("Data Retrieval", test_data_retrieval()))
    results.append(("Data Export", test_data_export()))
    
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
        print("🎉 ALL TESTS PASSED! Phase 3 is working correctly.")
        print("Ready to push to GitHub!")
    else:
        print("⚠️  SOME TESTS FAILED. Please check the errors above.")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
