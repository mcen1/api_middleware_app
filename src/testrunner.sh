echo "Launching uvicorn..."
source .env 
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
sleep 10
