import os
import subprocess
from pathlib import Path

def show_menu():
    print("\n=== Morocco Data Filter ===")
    print("1. Run Filter Pipeline")
    print("2. Exit")
    
    choice = input("Enter your choice (1-2): ").strip()
    return choice

def run_filter_pipeline():
    # Get the directory of this script
    script_dir = Path(__file__).parent
    
    # Define the paths to your filter scripts (assuming they're in the same directory)
    filter1_path = script_dir / "First_Data_Filter.py"
    filter2_path = script_dir / "Second_Data_Filter.py"
    filter3_path = script_dir / "third_Data_Filter.py"
    
    # Check if scripts exist
    if not all([filter1_path.exists(), filter2_path.exists(), filter3_path.exists()]):
        print("Error: One or more filter scripts are missing!")
        return
    
    # Run the scripts in sequence
    try:
        print("\nRunning Filter 1...")
        subprocess.run(["python", str(filter1_path)], check=True)
        
        print("\nRunning Filter 2...")
        subprocess.run(["python", str(filter2_path)], check=True)
        
        print("\nRunning Filter 3...")
        subprocess.run(["python", str(filter3_path)], check=True)
        
        print("\nAll filters completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error running filters: {e}")

def main():
    while True:
        choice = show_menu()
        
        if choice == '1':
            run_filter_pipeline()
        elif choice == '2':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()