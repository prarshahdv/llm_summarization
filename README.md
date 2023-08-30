# LLM Summarization App

Welcome to the LLM Summarization App repository! This application that summarizes and answers questions on uploaded files.

## Prerequisites

Before you can run the app, please ensure you have the following prerequisites installed on your system:

- **Python**: You'll need Python installed to run the application locally. You can download Python from [python.org](https://www.python.org/downloads/).

- **Docker**: Docker is required to containerize and run the application. You can download and install Docker from [docker.com](https://www.docker.com/products/docker-desktop).

## Getting Started

Follow these steps to get the Clinical Trial App up and running:

1. **Clone the Repository**:
```
git clone https://gitlab.com/prar_shah_dv/llm_summarization.git

cd llm_summarization
   ```
2. **Build the Docker image**
```
docker build -t your-image-name .
```

3. **Setup .env file**
```
OPENAI_API_KEY=your-api-key-here
```

4. **Run the Docker Container**
```
docker run -p 8561:8561 --env-file .env your-image-name
```

## Demo

Check out the live demo of the App:

[Demo Link](https://clinical-trials-jq4bjcqz4beoxu9lynij6g.streamlit.app/)