README
In order to run locally, follow these steps:


In powershell:
> Get-Process | Where-Object { $_.ProcessName -like "*ollama*" } | Stop-Process -Force
> ollama serve

In anaconda prompt:
> conda activate food_macro_tracker
> cd C:\Users\batzi\Food Macro Tracker
> uvicorn food_macros_api:app --reload

In terminal in jupyter notebook:
> streamlit run streamlit_app.py


Database is so far hosted locally, so is the app. 

Next up features:
- Renamed Page Sections 
- Save entries in Macro Counter and Target Macros in session state or for user
