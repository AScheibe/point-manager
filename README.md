# Points Management Application

This is a simple Flask-based application for managing transactions and points. 

## Prerequisites
1. [Python 3](https://python.org/downloads/) 
2. [pip](https://pip.pypa.io/en/stable/installation/)

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the App**:
   ```bash
   python3 run.py
   ```

3. **Running Tests**:
   ```bash
   python3 -m unittest test.py
   ```

## Endpoints

1. **/add**: This endpoint allows you to add transactions.
2. **/spend**: Use this endpoint to spend points.
3. **/balance**: Retrieve the current balance.
4. **/reset**: Resets certain global variables (used in development when running subsequent tests).

Please refer to `app.py` for more details on request and response formats.