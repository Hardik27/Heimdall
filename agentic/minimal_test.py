"""
Minimal test script to verify the core components work.
This script has minimal dependencies to help troubleshoot import issues.
"""
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test the import paths and print the Python environment details."""
    print("Python Environment Information:")
    print(f"Python Version: {sys.version}")
    print(f"Current Working Directory: {os.getcwd()}")
    print(f"sys.path: {sys.path}")
    print("-" * 80)
    
    # Try importing pydantic directly
    try:
        import pydantic
        print(f"Successfully imported pydantic version: {pydantic.__version__}")
    except ImportError as e:
        print(f"Failed to import pydantic: {e}")
    
    # Try importing other key dependencies
    dependencies = [
        "langchain", 
        "langchain_core", 
        "langgraph", 
        "flask", 
        "sqlalchemy", 
        "requests"
    ]
    
    print("\nPackage Import Status:")
    for package in dependencies:
        try:
            module = __import__(package)
            if hasattr(module, "__version__"):
                print(f"✅ {package}: {module.__version__}")
            else:
                print(f"✅ {package}: successfully imported (no version info)")
        except ImportError as e:
            print(f"❌ {package}: {e}")
    
    print("-" * 80)
    return True

def main():
    """Run the minimal test."""
    print("Running minimal test to check environment...")
    
    # Test imports
    test_imports()
    
    # Create a simple data structure
    user_data = {
        "phone_number": "+1234567890",
        "name": "Test User",
        "date_of_birth": "1980-01-01",
        "intent": "appointment_scheduling"
    }
    
    print("\nTest Data Structure:")
    for key, value in user_data.items():
        print(f"{key}: {value}")
    
    print("\nMinimal test completed successfully!")

if __name__ == "__main__":
    main()
