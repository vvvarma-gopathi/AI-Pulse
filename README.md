# 🚀 AI Pulse – AI-Powered Research & Project Discovery Platform

**AI Pulse** is an AI-powered research and project discovery platform designed to help developers explore emerging technologies, discover existing products and open-source projects, analyze industry trends, and generate innovative project ideas.

Instead of depending entirely on an LLM's internal knowledge, AI Pulse combines real-time internet search, external project discovery, Gemini-powered intelligence, Retrieval-Augmented Generation (RAG), and persistent database storage to provide research-driven insights.

🌐 **Live Application:** https://ai-pulse-frontend-orcin.vercel.app/

---

## ✨ Key Features

### 1. Internet Research & Technology Discovery
- Performs internet searches to discover relevant technologies, products, startups, and emerging trends.
- Integrates Talivy Search for external project and product discovery.
- Retrieves information from external sources rather than relying exclusively on LLM knowledge.
- Extracts and processes web content for research and analysis.

### 2. AI-Powered Analysis & Idea Generation
- Integrates Google's Gemini models for intelligent content analysis.
- Analyzes discovered technologies, products, and existing solutions.
- Identifies opportunities for improvement and potential use cases.
- Generates new project ideas based on research findings.
- Uses retrieved information as context for more relevant AI-generated responses.

### 3. WebSocket-Based Real-Time Communication
- Establishes persistent WebSocket connections between the frontend and backend.
- Enables continuous, bidirectional communication.
- Supports real-time data sharing and updates without repeatedly establishing HTTP requests.
- Helps maintain an interactive research experience.

### 4. RAG-Based Personal Project Intelligence
- Implements Retrieval-Augmented Generation to work with personal project information.
- Extracts and processes relevant project features and information.
- Retrieves relevant project context before generating LLM responses.
- Enables context-aware analysis using information from existing projects.

### 5. PostgreSQL Database Integration
- Uses PostgreSQL for persistent application data storage.
- Stores research-related information, article summaries, and technology metadata.
- Supports structured data retrieval and management.
- Separates persistent storage from real-time communication.

---

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core backend development |
| FastAPI | REST API development and backend orchestration |
| PostgreSQL | Persistent relational database |
| SQLAlchemy | Database interaction and ORM |
| Google Gemini | LLM-based analysis and idea generation |
| Talivy Search | Internet search and project discovery |
| RAG | Context-aware retrieval and project intelligence |
| WebSockets | Persistent, bidirectional real-time communication |
| Crawl4AI | Web crawling and content extraction |
| Trafilatura | Article and web content extraction |
| BeautifulSoup | HTML parsing and content processing |
| React | Frontend application |
| Vercel | Frontend hosting |

---

## 🏗️ Implementation Architecture

AI Pulse follows a modular architecture in which the frontend communicates with the backend, while the backend coordinates external search services, LLM integrations, retrieval mechanisms, and database operations.

### High-Level Architecture

```mermaid
flowchart TD
    A[User] --> B[React Frontend]

    B <-->|REST API| C[FastAPI Backend]
    B <-->|WebSocket| C

    C --> D[Research & Discovery Service]
    C --> E[Gemini LLM Service]
    C --> F[RAG Pipeline]
    C --> G[Database Layer]

    D --> H[Internet Search]
    D --> I[Talivy Project Discovery]
    D --> J[Web Crawling & Extraction]

    J --> K[Content Processing]

    H --> E
    I --> E
    K --> E

    F --> L[Personal Project Data]
    L --> M[Feature Extraction & Retrieval]
    M --> E

    G --> N[(PostgreSQL)]

    E --> C
    C --> B
```

### Architecture Components

#### 1. Frontend Layer
The React frontend provides the user interface for interacting with research, project discovery, and AI-powered features.

Responsibilities:
- Collecting user queries.
- Displaying research results.
- Presenting discovered projects and technologies.
- Communicating with backend APIs.
- Maintaining real-time communication through WebSockets.

#### 2. Backend Layer – FastAPI
FastAPI acts as the central application layer.

Responsibilities:
- Handling incoming API requests.
- Managing application workflows.
- Coordinating search and discovery services.
- Integrating Gemini models.
- Managing WebSocket connections.
- Communicating with PostgreSQL.
- Coordinating RAG-based retrieval.

#### 3. Internet Search & Project Discovery
The research and discovery layer retrieves external information.

Workflow:
1. Receive the user's research query.
2. Perform internet searches.
3. Discover relevant products, startups, and open-source projects using Talivy Search.
4. Crawl and extract relevant web content.
5. Process the retrieved information.
6. Pass relevant research context to the LLM.

#### 4. Gemini LLM Integration
Google Gemini handles the intelligence and generation layer.

Workflow:
1. Receive user instructions and retrieved research context.
2. Analyze the available information.
3. Identify important technologies, features, and opportunities.
4. Generate structured insights and project ideas.
5. Return the generated output to the backend.

#### 5. RAG Pipeline
The RAG implementation provides intelligence based on personal project information.

Workflow:

1. Collect personal project information.
2. Extract relevant project features and details.
3. Process project information for retrieval.
4. Retrieve relevant context based on the user's query.
5. Provide the retrieved context to the Gemini model.
6. Generate responses grounded in the available project information.

#### 6. Database Layer – PostgreSQL
PostgreSQL provides persistent storage for application data.

Responsibilities:
- Storing research results and article summaries.
- Maintaining technology metadata.
- Supporting structured data retrieval.
- Providing persistent storage for application information.

---

## 🔄 Overall Application Workflow

```mermaid
flowchart TD
    A[User Enters Query] --> B[React Frontend]
    B --> C[FastAPI Backend]

    C --> D{Query Type}

    D -->|Internet Research| E[Internet Search]
    D -->|Project Discovery| F[Talivy Search]
    D -->|Personal Projects| G[RAG Retrieval]
    D -->|Idea Generation| H[Gemini LLM]

    E --> I[Process Retrieved Information]
    F --> I
    G --> J[Retrieve Project Context]

    I --> H
    J --> H

    H --> K[Generate Insights or Ideas]
    K --> L[Store Relevant Data in PostgreSQL]
    L --> M[Return Results to Frontend]

    M --> N[Display Results to User]
```

---

## 💻 Installation & Setup

Follow these steps to configure the project locally.

### Prerequisites

Make sure you have the following installed:

- Python 3.10+
- Node.js and npm
- PostgreSQL
- Git
- Google Gemini API key
- Talivy Search API credentials

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd AI-Pulse
```

### 2. Backend Setup

Navigate to the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment.

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the backend directory.

Configure the required environment variables according to your application's settings:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/ai_pulse

GEMINI_API_KEY=your_gemini_api_key

TALIVY_API_KEY=your_talivy_api_key
```

Replace the example values with your actual credentials and match the variable names to those used in your configuration.

**Important:** Never commit API keys, database credentials, or `.env` files to GitHub.

### 4. PostgreSQL Configuration

Create a PostgreSQL database:

```sql
CREATE DATABASE ai_pulse;
```

Configure the database connection string in your environment variables.

Ensure that the database schema and required tables are initialized using the project's database initialization process.

### 5. Start the Backend

Run the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

Backend API documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Frontend Setup

Open another terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install frontend dependencies:

```bash
npm install
```

Configure the backend API URL and WebSocket URL using the environment variable names expected by your frontend.

Start the frontend development server:

```bash
npm run dev
```

The frontend will be available at the local development URL printed by the development server.

---

## ☁️ Deployment

AI Pulse is deployed and accessible online.

| Component | Hosting |
|---|---|
| Frontend | Vercel |
| Backend | Backend deployment configuration |
| Database | PostgreSQL |

### Live Application

🌐 https://ai-pulse-frontend-orcin.vercel.app/

---

## 🎯 Engineering Concepts Demonstrated

This project demonstrates practical implementation of several full-stack and Generative AI engineering concepts:

- Full-stack application development using React and FastAPI.
- REST API architecture and backend service orchestration.
- External API integrations and real-time internet search.
- LLM integration using Google Gemini models.
- AI-powered research and automated idea generation.
- Retrieval-Augmented Generation (RAG).
- Context-aware information retrieval.
- WebSocket-based bidirectional communication.
- Relational database integration using PostgreSQL.
- Web crawling, HTML parsing, and content extraction.
- Deployment and environment-based application configuration.

---

## 📌 Future Enhancements

Potential improvements for the platform include:

- Advanced research workflows with multi-step search.
- Improved source verification and research citations.
- Enhanced semantic retrieval for personal project information.
- Research history and advanced filtering.
- Background processing for large research tasks.
- More advanced project recommendation mechanisms.

---

## 👨‍💻 Author

**Gopathi Vishnu Vardhan Varma**

Python Full-Stack Developer | Generative AI Enthusiast

- Portfolio: https://varmadev.in
- GitHub: https://github.com/vvvarma-gopathi
- LinkedIn: https://www.linkedin.com/in/vvvarma66

---

⭐ If you find this project interesting, feel free to explore the live application and connect with me!
