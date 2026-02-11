import sys
import os

try:
    from .service import run_analysis
except ImportError:
    from service import run_analysis

def run():
    ticker = os.getenv("COMPANY_STOCK", "AMZN")
    return run_analysis(ticker)

def train():
    """
    Kept for compatibility.
    """
    ticker = os.getenv("COMPANY_STOCK", "AMZN")
    try:
        print(run_analysis(ticker))
    except Exception as e:
        raise Exception(f"An error occurred while running analysis: {e}")
    
if __name__ == "__main__":
    print("## Welcome to Stock Analysis Crew")
    print('-------------------------------')
    result = run()
    print("\n\n########################")
    print("## Here is the Report")
    print("########################\n")
    print(result)
