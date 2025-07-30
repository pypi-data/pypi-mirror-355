import requests
import pandas as pd
from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime, date
import os
from pathlib import Path

class OneAlphaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def _validate_dates(self, start_date: str, end_date: str) -> tuple[str, str]:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            if start > end:
                raise ValueError("start_date must be before end_date")
            return start_date, end_date
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD. Error: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        try:
            response = self.session.get(f"{self.base_url}/test-connection")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Connection test failed: {str(e)}")

    def configure(self, database_url: str) -> Dict[str, Any]:
        try:
            payload = {"database_url": database_url}
            response = self.session.post(f"{self.base_url}/configure", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Configuration failed: {str(e)}")

    def validate_symbols(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        frequency: str = "15min",
        *,
        symbol_names: List[str] = None,
        date_range: Tuple[str, str] = None
    ) -> Dict[str, Any]:
        symbols = symbols or symbol_names
        if not symbols:
            raise ValueError("Either 'symbols' or 'symbol_names' must be provided")

        if date_range:
            if start_date or end_date:
                raise ValueError("Provide either 'date_range' or 'start_date' and 'end_date', not both")
            start_date, end_date = date_range
        elif not (start_date and end_date):
            raise ValueError("Either 'date_range' or both 'start_date' and 'end_date' must be provided")

        start_date, end_date = self._validate_dates(start_date, end_date)
        
        payload = {
            "symbols": symbols,
            "start_date": start_date,
            "end_date": end_date,
            "frequency": frequency,
            "format_type": "merged",
            "fields": ["close"]
        }
        
        try:
            response = self.session.post(f"{self.base_url}/validate", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Symbol validation failed: {str(e)}")

    def fetch_dataframe(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        frequency: str = "15min",
        format_type: str = "merged",
        fields: Optional[List[str]] = None,
        *,
        symbol_names: List[str] = None,
        date_range: Tuple[str, str] = None,
        type: str = None
    ) -> pd.DataFrame:
        symbols = symbols or symbol_names
        if not symbols:
            raise ValueError("Either 'symbols' or 'symbol_names' must be provided")

        if date_range:
            if start_date or end_date:
                raise ValueError("Provide either 'date_range' or 'start_date' and 'end_date', not both")
            start_date, end_date = date_range
        elif not (start_date and end_date):
            raise ValueError("Either 'date_range' or both 'start_date' and 'end_date' must be provided")

        format_type = format_type if type is None else type

        start_date, end_date = self._validate_dates(start_date, end_date)
        
        if fields is None:
            fields = ["close"]
        
        payload = {
            "symbols": symbols,
            "start_date": start_date,
            "end_date": end_date,
            "frequency": frequency,
            "format_type": format_type,
            "fields": fields
        }
        
        try:
            response = self.session.post(f"{self.base_url}/data/json", json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("message") == "No data found":
                columns = ['Date', 'Timestamp', 'Time']
                if format_type == "individual":
                    columns.extend([field.capitalize() for field in fields] + ['Volume'])
                else:
                    for symbol in symbols:
                        for field in fields:
                            columns.append(f"{symbol}_{field}")
                return pd.DataFrame(columns=columns)
            
            df = pd.DataFrame(result["data"])
            
            if not df.empty:
                for col in df.columns:
                    if col.lower() in ['date', 'time', 'timestamp']:
                        continue
                    if col.lower() == 'volume':
                        df[col] = df[col].astype('int64')
                    elif col not in ['Ticker']:
                        df[col] = df[col].astype('float64')
            
            return df
        
        except requests.RequestException as e:
            raise Exception(f"Data fetch failed: {str(e)}")

    def fetch_csv(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        frequency: str = "15min",
        format_type: str = "merged",
        fields: Optional[List[str]] = None,
        *,
        symbol_names: List[str] = None,
        date_range: Tuple[str, str] = None,
        type: str = None,
        output_dir: str = None
    ) -> Union[List[str], str]:
        symbols = symbols or symbol_names
        if not symbols:
            raise ValueError("Either 'symbols' or 'symbol_names' must be provided")

        if date_range:
            if start_date or end_date:
                raise ValueError("Provide either 'date_range' or 'start_date' and 'end_date', not both")
            start_date, end_date = date_range
        elif not (start_date and end_date):
            raise ValueError("Either 'date_range' or both 'start_date' and 'end_date' must be provided")

        format_type = format_type if type is None else type

        start_date, end_date = self._validate_dates(start_date, end_date)
        
        if fields is None:
            fields = ["close"]
        
        payload = {
            "symbols": symbols,
            "start_date": start_date,
            "end_date": end_date,
            "frequency": frequency,
            "format_type": format_type,
            "fields": fields
        }
        
        try:
            response = self.session.post(f"{self.base_url}/data/csv", json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get("message") == "No data found":
                raise Exception("No data found to save as CSV")
            
            df = pd.DataFrame(result["data"])
            
            if df.empty:
                raise Exception("No data found to save as CSV")
            
            save_path = os.path.join(str(Path.home()), "Downloads", "onealpha_data")
            os.makedirs(save_path, exist_ok=True)
            
            start_date_str = start_date.replace('-', '')
            end_date_str = end_date.replace('-', '')
            
            if format_type == "individual":
                individual_csv_path = os.path.join(save_path, "individual_csv")
                os.makedirs(individual_csv_path, exist_ok=True)
                paths = []
                
                for symbol in symbols:
                    ticker = symbol.upper()
                    symbol_df = df[df['Ticker'] == ticker] if 'Ticker' in df.columns else pd.DataFrame()
                    
                    if not symbol_df.empty:
                        file_name = f"{ticker}_{frequency}_{start_date_str}_{end_date_str}.csv"
                        file_path = os.path.join(individual_csv_path, file_name)
                        symbol_df.to_csv(file_path, index=False)
                        paths.append(file_path)
                
                if not paths:
                    raise Exception("No data found for any symbols to save as CSV")
                return paths
            else:
                file_name = f"MERGED_{frequency}_{start_date_str}_{end_date_str}.csv"
                file_path = os.path.join(save_path, file_name)
                df.to_csv(file_path, index=False)
                return file_path
                
        except requests.RequestException as e:
            raise Exception(f"CSV fetch failed: {str(e)}")
        except Exception as e:
            raise Exception(f"CSV save failed: {str(e)}")

    def get_available_symbols(self) -> Dict[str, Any]:
        try:
            response = self.session.get(f"{self.base_url}/symbols")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch available symbols: {str(e)}")

# Create a default instance for convenience
client = None  # Set to None since base_url is now required

# Expose top-level functions for easier imports
def test_connection() -> Dict[str, Any]:
    if client is None:
        raise ValueError("Client not initialized. Please create an instance of OneAlphaClient with a valid base_url.")
    return client.test_connection()

def configure(database_url: str) -> Dict[str, Any]:
    if client is None:
        raise ValueError("Client not initialized. Please create an instance of OneAlphaClient with a valid base_url.")
    return client.configure(database_url)

def validate_symbols(
    symbols: List[str] = None,
    start_date: str = None,
    end_date: str = None,
    frequency: str = "15min",
    *,
    symbol_names: List[str] = None,
    date_range: Tuple[str, str] = None
) -> Dict[str, Any]:
    if client is None:
        raise ValueError("Client not initialized. Please create an instance of OneAlphaClient with a valid base_url.")
    return client.validate_symbols(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        symbol_names=symbol_names,
        date_range=date_range
    )

def fetch_dataframe(
    symbols: List[str] = None,
    start_date: str = None,
    end_date: str = None,
    frequency: str = "15min",
    format_type: str = "merged",
    fields: Optional[List[str]] = None,
    *,
    symbol_names: List[str] = None,
    date_range: Tuple[str, str] = None,
    type: str = None
) -> pd.DataFrame:
    if client is None:
        raise ValueError("Client not initialized. Please create an instance of OneAlphaClient with a valid base_url.")
    return client.fetch_dataframe(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        format_type=format_type,
        fields=fields,
        symbol_names=symbol_names,
        date_range=date_range,
        type=type
    )

def fetch_csv(
    symbols: List[str] = None,
    start_date: str = None,
    end_date: str = None,
    frequency: str = "15min",
    format_type: str = "merged",
    fields: Optional[List[str]] = None,
    *,
    symbol_names: List[str] = None,
    date_range: Tuple[str, str] = None,
    type: str = None,
    output_dir: str = None
) -> Union[List[str], str]:
    if client is None:
        raise ValueError("Client not initialized. Please create an instance of OneAlphaClient with a valid base_url.")
    return client.fetch_csv(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        format_type=format_type,
        fields=fields,
        symbol_names=symbol_names,
        date_range=date_range,
        type=type,
        output_dir=output_dir
    )

def get_available_symbols() -> Dict[str, Any]:
    if client is None:
        raise ValueError("Client not initialized. Please create an instance of OneAlphaClient with a valid base_url.")
    return client.get_available_symbols()