"""
Example usage of the database module
Demonstrates how to use CRUD operations
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.connection import get_db_connection, get_session
from src.database import crud
from src.database.init_db import init_database


def example_usage():
    """Example demonstrating database usage"""
    
    # Initialize database
    print("Initializing database...")
    init_database()
    
    # Get a session
    session = get_session()
    
    try:
        # Example 1: Insert a patient
        print("\n1. Inserting a patient...")
        patient = crud.insert_patient_data(
            session=session,
            age=18393,  # ~50 years in days
            gender=2,  # Male
            height=175.0,
            weight=75.0,
            name="John Doe"
        )
        print(f"   Created patient with ID: {patient.patient_id}")
        
        # Example 2: Insert health metrics
        print("\n2. Inserting health metrics...")
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
        print(f"   Created health metric with ID: {metric.metric_id}")
        
        # Example 3: Retrieve patient
        print("\n3. Retrieving patient...")
        patients = crud.retrieve_patient_data(session, patient_id=patient.patient_id)
        if patients:
            p = patients[0]
            print(f"   Patient: {p.name}, Age: {p.age} days, Height: {p.height} cm, Weight: {p.weight} kg")
        
        # Example 4: Update patient
        print("\n4. Updating patient weight...")
        updated = crud.update_patient_data(
            session=session,
            patient_id=patient.patient_id,
            weight=78.0
        )
        print(f"   Updated weight to: {updated.weight} kg")
        
        # Example 5: Insert correlation result
        print("\n5. Inserting correlation result...")
        correlation = crud.insert_correlation_result(
            session=session,
            metric1="systolic_bp",
            metric2="cholesterol",
            correlation_value=0.65,
            correlation_type="pearson",
            sample_size=1000
        )
        print(f"   Created correlation result with ID: {correlation.correlation_id}")
        
        # Example 6: Insert medical image metadata
        print("\n6. Inserting medical image metadata...")
        image = crud.insert_image_metadata(
            session=session,
            filename="chest_xray.jpg",
            image_path="/data/images/chest_xray.jpg",
            image_type="X-ray",
            patient_id=patient.patient_id
        )
        print(f"   Created image record with ID: {image.image_id}")
        
        print("\n✅ All examples completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    example_usage()
