# Emori GenAI

A simple GenAI project with MongoDB integration, user management, and semantic search support.

---

## 🔌 Connection to MongoDB
```bash
mongodb://host.docker.internal:27017/
```

---

## ▶️ How to Run

```bash
cd agents_Emori/
python main.py
```

To quit:
```bash
quit
```

---

## 👤 User Management
Create or delete users with:

```bash
cd agents_Emori/
python user_manager.py
```

---

## 💬 Flow
1. Insert `id` → press **Enter**  
2. Insert `message` → press **Enter**  

---

## 🔍 Semantic Search
Semantic search requires developer-provided **URI** and **Token**.  

---

## ⚙️ Environment Variables (`.env` file)
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

## 🐳 Docker Setup

Build the image:
```bash
docker build -t <your-docker-name> .
```

Run the container:
```bash
docker run -d -p 8888:8888 --name mycontainer myapp
```

---

## 📌 Notes
- Ensure MongoDB is running locally or update the connection string.  
- `.env` is recommended for sensitive values (API keys, tokens).  
