import sys

from .validate_files import process_and_validate_files
from .llm_setup import get_api_key_model
from .generate_data import generate_synthetic_data
from .output import generate_ouput


def get_csv_data():

    # Process and validate files
    args = sys.argv[1:]
    config, reference_file = process_and_validate_files(args)

    # Get Provider, API Key and Model
    provider, api_key, model = get_api_key_model()
    
    # Generate synthetic data
    df = generate_synthetic_data(config, reference_file, provider, api_key, model)
    
    # Save Synthetic data
    generate_ouput(df)

if __name__ == "__main__":
    get_csv_data()
