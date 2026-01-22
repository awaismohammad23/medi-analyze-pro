"""
Example usage of the data processing module
Demonstrates CSV loading, validation, import, retrieval, and export
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.data_processing import CSVLoader, DataImporter, DataRetriever, DataExporter
from src.database import get_session, init_database


def example_csv_loading():
    """Example: Load and validate CSV file"""
    print("=" * 60)
    print("Example 1: CSV Loading and Validation")
    print("=" * 60)
    
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'datasets',
        'cardio_train.csv'
    )
    
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return
    
    # Load CSV
    loader = CSVLoader()
    df, errors = loader.load_and_validate(csv_path, strict_validation=False)
    
    print(f"\nLoaded {len(df)} rows")
    print(f"Columns: {list(df.columns)[:5]}...")
    print(f"Validation errors: {len(errors)}")
    
    if errors:
        print(f"\nFirst 3 errors:")
        for err in errors[:3]:
            print(f"  - {err}")


def example_data_import():
    """Example: Import CSV data to database"""
    print("\n" + "=" * 60)
    print("Example 2: Data Import to Database")
    print("=" * 60)
    
    # Initialize database
    init_database()
    
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'datasets',
        'cardio_train.csv'
    )
    
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return
    
    # Import data (limit to first 100 rows for demo)
    session = get_session()
    importer = DataImporter(session=session, batch_size=50)
    
    def progress_callback(processed, total, message):
        print(f"  {message}: {processed}/{total} rows")
    
    print("\nImporting data...")
    stats = importer.import_from_csv(
        csv_path,
        create_patients=True,
        create_health_metrics=True,
        progress_callback=progress_callback
    )
    
    print(f"\nImport Statistics:")
    print(f"  Total rows processed: {stats['total_rows']}")
    print(f"  Patients created: {stats['patients_created']}")
    print(f"  Patients skipped: {stats['patients_skipped']}")
    print(f"  Health metrics created: {stats['health_metrics_created']}")
    print(f"  Health metrics skipped: {stats['health_metrics_skipped']}")
    print(f"  Errors: {len(stats['errors'])}")
    
    session.close()


def example_data_retrieval():
    """Example: Retrieve data from database"""
    print("\n" + "=" * 60)
    print("Example 3: Data Retrieval")
    print("=" * 60)
    
    session = get_session()
    retriever = DataRetriever(session=session)
    
    # Get all patients
    patients = retriever.get_patients(limit=5)
    print(f"\nRetrieved {len(patients)} patients (limited to 5)")
    
    if patients:
        print(f"\nFirst patient:")
        p = patients[0]
        print(f"  ID: {p.patient_id}")
        print(f"  Age: {p.age} days")
        print(f"  Gender: {p.gender}")
        print(f"  Height: {p.height} cm")
        print(f"  Weight: {p.weight} kg")
    
    # Get health metrics
    metrics = retriever.get_health_metrics(limit=5)
    print(f"\nRetrieved {len(metrics)} health metrics (limited to 5)")
    
    if metrics:
        print(f"\nFirst health metric:")
        m = metrics[0]
        print(f"  Patient ID: {m.patient_id}")
        print(f"  Systolic BP: {m.systolic_bp}")
        print(f"  Diastolic BP: {m.diastolic_bp}")
    
    # Get statistics
    stats = retriever.get_statistics()
    print(f"\nDatabase Statistics:")
    print(f"  Total patients: {stats.get('total_patients', 0)}")
    print(f"  Total health metrics: {stats.get('total_health_metrics', 0)}")
    if stats.get('avg_systolic_bp'):
        print(f"  Average systolic BP: {stats['avg_systolic_bp']:.1f}")
    
    session.close()


def example_data_export():
    """Example: Export data to CSV"""
    print("\n" + "=" * 60)
    print("Example 4: Data Export")
    print("=" * 60)
    
    session = get_session()
    retriever = DataRetriever(session=session)
    exporter = DataExporter(retriever=retriever)
    
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'data',
        'processed'
    )
    os.makedirs(output_dir, exist_ok=True)
    
    # Export patients
    patients_path = os.path.join(output_dir, 'exported_patients.csv')
    success = exporter.export_patients_to_csv(patients_path, limit=10)
    if success:
        print(f"\n✅ Exported patients to: {patients_path}")
    
    # Export health metrics
    metrics_path = os.path.join(output_dir, 'exported_metrics.csv')
    success = exporter.export_health_metrics_to_csv(metrics_path, limit=10)
    if success:
        print(f"✅ Exported health metrics to: {metrics_path}")
    
    session.close()


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("MediAnalyze Pro - Data Processing Module Examples")
    print("=" * 60)
    
    try:
        example_csv_loading()
        example_data_import()
        example_data_retrieval()
        example_data_export()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
