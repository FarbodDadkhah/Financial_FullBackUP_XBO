import uvicorn
from app.main import create_app

app = create_app()

if __name__ == "__main__":
    print("Starting Customer Service Support System...")
    print("Rep View:  http://localhost:8000/rep")
    print("Dashboard: http://localhost:8000/dashboard")
    uvicorn.run(app, host="0.0.0.0", port=8000)
