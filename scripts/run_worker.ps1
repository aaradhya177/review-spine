$env:PYTHONPATH = "backend"
python -m arq app.job_queue.arq_worker.WorkerSettings

