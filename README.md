# Emori Gen AI

Emori Gen AI is an AI chatbot companion with **two semantic search integrations**:  

1. **Context Retrieval (RAG)** – for finding relevant information.  
2. **Classification** – for detecting potential mental health problems.  

It analyzes each user query with **sentiment analysis** and **self-evaluation** to provide accurate and context-aware responses.

---
## Full WorkFlow
generated via Pyppeteer
![Full Graph Workflow](https://github.com/user-attachments/assets/ed82345b-6ede-4c77-9267-6896a9ff5ecd)

---

## Features

- **AI Chatbot**: Interactive conversational agent.  
- **Two Semantic Searches**:
  - **Semantic Search 1 (RAG)**: Finds related data from research papers, conversation data, articles, and reports.  
  - **Semantic Search 2**: Compares user queries to labeled text data to detect mental health issues.  
- **Top-k Filter**: Filters out irrelevant results from Semantic Search 2 and uses LLMs to ensure relevance before processing.  
- **Sentiment Score**: Analyzes user queries to provide sentiment scores (positive, negative, neutral) and categorizes the query type.  
- **Flag Generator**: Detects potential mental health concerns and signals the answer generator.  
- **Calculator**: Computes sentiment and document similarity scores, including decay and past scores, for complex evaluation.  
- **Label Generator**: Categorizes user queries to narrow down context and improve relevance for Semantic Search 1.  
- **Answer Generator**: Uses LLMs to generate answers based on flagged concerns and retrieved relevant documents.  
- **Memory**: Remembers past conversations, scores, and mental health context.  
- **Self-Evaluation**: LLM-based evaluation of generated answers; if the score falls below a threshold, feedback is generated and looped back to improve the answer.

---

## How It Works

1. **User Query Flow**:
   - Insert `id` → press Enter  
   - Insert `message` → press Enter  

2. **Semantic Search**:
   - Search 1 finds related context (RAG).  
   - Search 2 analyzes similarity with labeled mental health data.  
   - Top-k filter removes irrelevant results.  

3. **Analysis & Generation**:
   - Sentiment and similarity scores are calculated.  
   - Flags are generated for possible mental health concerns.  
   - Answer generator creates response using context from flagged concerns and retrieved documents.  
   - Self-evaluation checks answer quality and loops back for improvements if necessary.

---

## Connection to MongoDB
```bash
mongodb://host.docker.internal:27017/
```

---

## Environment Variables

Create a `.env` file with the following keys:

```
ZILLIZ_URI_B=
ZILLIZ_TOKEN_B=
OPENAI_API_KEY=
```

Alternatively, set them in your terminal:

```bash
export ZILLIZ_URI="your_uri_here"
export ZILLIZ_TOKEN="your_token_here"
```

Check values:

```bash
echo $ZILLIZ_URI
echo $ZILLIZ_TOKEN
```

---

## Running the Project

### Run the Chatbot
```bash
cd agents_Emori/
python main.py
```
To quit:
```bash
quit
```

### Manage Users
```bash
cd agents_Emori/
python user_manager.py
```

---

## Docker Setup

Build the Docker image:

```bash
docker build -t <your-docker-name> .
```

Run the container:

```bash
docker run -d -p 8888:8888 --name mycontainer myapp
```

---

## Notes

- Ensure MongoDB is running locally or update the connection string.  
- `.env` is recommended for storing sensitive values (API keys, tokens).  
- Memory and self-evaluation enable the chatbot to improve responses over time.  
