# AI Text Processor

A Flask web application that processes text using OpenAI's ChatGPT API with customizable parameters controlled by sliders.

## Features

- **Text Input**: Paste text directly or upload .txt/.md files
- **Customizable Processing**: Four sliders to control:
  - Faithfulness to Original (1-10)
  - Human-like Sounding (1-10) 
  - AI-like Sounding (1-10)
  - Formality Level (1-10)
- **Rate Limiting**: Built-in protection against API abuse
- **Error Handling**: Comprehensive error handling and user feedback
- **Responsive Design**: Works on desktop and mobile devices

## Setup Instructions

### Local Development

1. **Clone and Setup**:
   \`\`\`bash
   git clone <repository-url>
   cd flask-text-processor
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   \`\`\`

2. **Environment Variables**:
   \`\`\`bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   \`\`\`

3. **Run Locally**:
   \`\`\`bash
   python app.py
   \`\`\`

### Deployment on Render

1. **Connect Repository**: Link your GitHub repository to Render

2. **Environment Variables**: Set in Render dashboard:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SECRET_KEY`: Random secret key for Flask sessions
   - `FLASK_ENV`: Set to "production"

3. **Deploy**: Render will automatically deploy using the `render.yaml` configuration

## API Usage

### POST /process

Process text with custom parameters.

**Parameters**:
- `text_input`: Text to process (string)
- `file`: Text file upload (optional)
- `faithfulness`: 1-10 scale
- `human_like`: 1-10 scale  
- `ai_like`: 1-10 scale
- `formality`: 1-10 scale

**Response**:
\`\`\`json
{
  "success": true,
  "original_text": "...",
  "processed_text": "...",
  "parameters": {
    "faithfulness": 5,
    "human_like": 7,
    "ai_like": 3,
    "formality": 6
  }
}
\`\`\`

## Security Features

- Rate limiting (50 requests/hour, 200/day)
- File upload validation
- Input sanitization
- Secure file handling
- Environment-based configuration

## Error Handling

- OpenAI API errors (rate limits, invalid requests)
- File upload errors (size, format)
- Input validation errors
- Network connectivity issues

## Technical Stack

- **Backend**: Flask, OpenAI API
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Deployment**: Render with Gunicorn
- **Security**: Flask-Limiter, Werkzeug
