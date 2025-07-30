import onealpha
import pandas as pd

def main():
    onealpha.client = onealpha.OneAlphaClient(base_url="http://localhost:8000")  # Replace with your desired URL
    try:
        # Test connection
        print("Testing connection...")
        connection_status = onealpha.test_connection()
        print(f"Connection status: {connection_status}")

        # Test validate symbols
        print("\nValidating symbols...")
        validation = onealpha.validate_symbols(
            symbols=['AARTIIND', 'RELIANCE', 'TCS'],
            start_date='2025-02-17',
            end_date='2025-02-22',
            frequency='1min'
        )
        print(f"Validation result: {validation}")

        # Test fetchDataFrame with different field combinations
        print("\nFetching DataFrame (merged, Open and High)...")
        df1 = onealpha.fetch_dataframe(
            symbols=['AARTIIND', 'RELIANCE', 'TCS'],
            start_date='2025-02-17',
            end_date='2025-02-22',
            frequency='1min',
            format_type='merged',
            fields=['Open', 'High']
        )
        print("DataFrame 1:")
        print(df1)

        print("\nFetching DataFrame (individual, all fields)...")
        df2 = onealpha.fetch_dataframe(
            symbols=['AARTIIND', 'RELIANCE', 'TCS'],
            start_date='2025-02-17',
            end_date='2025-02-22',
            frequency='1min',
            format_type='individual',
            fields=['open', 'high', 'low', 'close']
        )
        print("DataFrame 2:")
        print(df2)

        print("\nFetching DataFrame (merged, Close only)...")
        df3 = onealpha.fetch_dataframe(
            symbols=['AARTIIND', 'RELIANCE', 'TCS'],
            start_date='2025-02-17',
            end_date='2025-02-22',
            frequency='1min',
            format_type='merged',
            fields=['Close']
        )
        print("DataFrame 3:")
        print(df3)

        # Test fetchCSV
        print("\nFetching CSV...")
        csv_path = onealpha.fetch_csv(
            symbols=['AARTIIND', 'RELIANCE', 'TCS'],
            start_date='2025-02-17',
            end_date='2025-02-22',
            frequency='1min',
            format_type='merged',
            fields=['Open', 'High', 'Low', 'Close']
        )
        print(f"File saved: {csv_path}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
    
    
    
    