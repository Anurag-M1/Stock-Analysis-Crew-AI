import sys
import os

try:
    from .crew import StockAnalysisCrew
except ImportError:
    from crew import StockAnalysisCrew

def run():
    ticker = os.getenv("COMPANY_STOCK", "AMZN")
    inputs = {
        "query": "What is the company you want to analyze?",
        "company_stock": ticker,
    }
    return StockAnalysisCrew().crew().kickoff(inputs=inputs)

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "query": "What is last years revenue",
        "company_stock": os.getenv("COMPANY_STOCK", "AMZN"),
    }
    try:
        StockAnalysisCrew().crew().train(n_iterations=int(sys.argv[1]), inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")
    
if __name__ == "__main__":
    print("## Welcome to Stock Analysis Crew")
    print('-------------------------------')
    result = run()
    print("\n\n########################")
    print("## Here is the Report")
    print("########################\n")
    print(result)
