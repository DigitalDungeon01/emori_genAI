FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install ipykernel and jupyter
RUN pip install --no-cache-dir ipykernel jupyter

# Copy the rest of the app
COPY . .

ENV PORT=8080

EXPOSE 8080
# Expose kernel ports (Jupyter uses these for kernel communication)
EXPOSE 8888

# Start Jupyter with kernel gateway mode
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser", "--NotebookApp.token=''", "--NotebookApp.password=''"]