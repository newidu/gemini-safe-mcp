FROM python:3.12-slim

WORKDIR /app

# අවශ්‍ය dependencies කොපි කර install කිරීම
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# server එක සහ අනෙකුත් අත්‍යවශ්‍ය files කොපි කිරීම
COPY server.py ./
RUN mkdir -p /data/workspace

# Environment variables
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8000
ENV MCP_WORKSPACE=/data/workspace

EXPOSE 8000

CMD ["python", "server.py"]
