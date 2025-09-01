from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import openai
import os
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure OpenAI
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'md'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_slider_values(data):
    """Validate that all slider values are integers between 0-10"""
    required_params = ['faithfulness', 'human_like', 'ai_like', 'formality']
    
    for param in required_params:
        try:
            value = int(data.get(param, 0))
            if not 0 <= value <= 10:
                return False, f"{param} must be between 0 and 10"
        except (ValueError, TypeError):
            return False, f"{param} must be a valid number"
    
    return True, None

def create_processing_prompt(text, faithfulness, human_like, ai_like, formality):
    """Create a detailed prompt for ChatGPT based on slider values"""
    
    # Build prompt based on slider values
    prompt_parts = [
        "Please process the following text according to these specific parameters:",
        f"\n**Faithfulness to Original (Level {faithfulness}/10):**"
    ]
    
    if faithfulness <= 2:
        prompt_parts.append("Make significant changes and improvements to the content while preserving core meaning.")
    elif faithfulness <= 5:
        prompt_parts.append("Make moderate changes to improve clarity and flow while keeping most original content.")
    else:
        prompt_parts.append("Make minimal changes, focusing only on essential corrections and improvements.")
    
    prompt_parts.append(f"\n**Human-like Sound (Level {human_like}/10):**")
    if human_like <= 2:
        prompt_parts.append("Use very natural, conversational language with contractions and casual expressions.")
    elif human_like <= 5:
        prompt_parts.append("Use moderately natural language that sounds human but polished.")
    else:
        prompt_parts.append("Use highly natural, warm, and engaging human language with personality.")
    
    prompt_parts.append(f"\n**AI-like Sound (Level {ai_like}/10):**")
    if ai_like <= 2:
        prompt_parts.append("Avoid any mechanical or robotic phrasing; sound completely human.")
    elif ai_like <= 5:
        prompt_parts.append("Use some structured phrasing but maintain natural flow.")
    else:
        prompt_parts.append("Use precise, structured language that sounds more systematic and analytical.")
    
    prompt_parts.append(f"\n**Formality Level (Level {formality}/10):**")
    if formality <= 2:
        prompt_parts.append("Use very casual, informal language appropriate for friends or social media.")
    elif formality <= 5:
        prompt_parts.append("Use moderately formal language suitable for business communication.")
    else:
        prompt_parts.append("Use highly formal, academic or professional language.")
    
    prompt_parts.extend([
        "\n**Text to process:**",
        f"\n{text}",
        "\n**Instructions:** Apply the above parameters to rewrite this text. Return only the processed text without explanations."
    ])
    
    return "".join(prompt_parts)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
@limiter.limit("10 per minute")
def process_text():
    try:
        # Check if OpenAI API key is configured
        if not openai.api_key:
            return jsonify({
                'success': False, 
                'error': 'OpenAI API key not configured. Please contact administrator.'
            }), 500
        
        # Get text input (either from form or file upload)
        text_input = request.form.get('text_input', '').strip()
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                try:
                    filename = secure_filename(file.filename)
                    file_content = file.read().decode('utf-8')
                    text_input = file_content if not text_input else text_input
                except UnicodeDecodeError:
                    return jsonify({
                        'success': False, 
                        'error': 'File must be valid UTF-8 text'
                    }), 400
        
        if not text_input:
            return jsonify({
                'success': False, 
                'error': 'Please provide text input or upload a text file'
            }), 400
        
        if len(text_input) > 10000:  # Limit text length
            return jsonify({
                'success': False, 
                'error': 'Text input too long. Maximum 10,000 characters allowed.'
            }), 400
        
        # Validate slider values
        is_valid, error_msg = validate_slider_values(request.form)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Get slider values
        faithfulness = int(request.form.get('faithfulness'))
        human_like = int(request.form.get('human_like'))
        ai_like = int(request.form.get('ai_like'))
        formality = int(request.form.get('formality'))
        
        # Create processing prompt
        processing_prompt = create_processing_prompt(
            text_input, faithfulness, human_like, ai_like, formality
        )
        
        # Call OpenAI API
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert writing coach and text editor with deep expertise in grammar, style, clarity, and tone. You excel at improving text while respecting the author's voice and intent. Follow the given parameters precisely to enhance the provided text with professional writing standards."},
                    {"role": "user", "content": processing_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            processed_text = response.choices[0].message.content.strip()
            
            # Log successful processing
            logger.info(f"Text processed successfully. Length: {len(text_input)} -> {len(processed_text)}")
            
            return jsonify({
                'success': True,
                'original_text': text_input,
                'processed_text': processed_text,
                'parameters': {
                    'faithfulness': faithfulness,
                    'human_like': human_like,
                    'ai_like': ai_like,
                    'formality': formality
                }
            })
            
        except openai.error.RateLimitError:
            return jsonify({
                'success': False, 
                'error': 'API rate limit exceeded. Please try again later.'
            }), 429
        except openai.error.InvalidRequestError as e:
            return jsonify({
                'success': False, 
                'error': f'Invalid request: {str(e)}'
            }), 400
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return jsonify({
                'success': False, 
                'error': 'Failed to process text. Please try again.'
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in process_text: {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'An unexpected error occurred. Please try again.'
        }), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False, 
        'error': 'File too large. Maximum size is 16MB.'
    }), 413

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'success': False, 
        'error': 'Rate limit exceeded. Please try again later.'
    }), 429

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
