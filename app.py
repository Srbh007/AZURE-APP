import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
import PyPDF2
import re
import openai
from azure.identity import DefaultAzureCredential

app = Flask(__name__)
app = Flask(__name__, static_folder='static')
app.config.from_object('config.Config')
db = SQLAlchemy(app)

# OpenAI Configuration with error handling
try:
    openai.api_type = "azure"
    openai.api_key = app.config['AZURE_OPENAI_API_KEY']
    openai.api_base = app.config['AZURE_OPENAI_ENDPOINT']
    openai.api_version = app.config['API_VERSION']
    DEPLOYMENT_NAME = app.config['DEPLOYMENT_NAME']
    logger.info("OpenAI configuration loaded successfully")
except Exception as e:
    logger.error(f"Error loading OpenAI configuration: {str(e)}")
    raise

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    chats = db.relationship('Chat', backref='user', lazy=True)

class Chat(db.Model):
    __tablename__ = 'chats'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    pdf_preview = db.Column(db.Boolean, default=False)
    embedded_website = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

def clean_response(text):
    text = re.sub(r'[\*\#]', '', text)
    return text.strip()

# Your existing keyword_links dictionary
keyword_links = {
    "Arduino": ["https://blog.arduino.cc/", "https://www.instructables.com/howto/Arduino/"],
    "Bluetooth Controlled Robot Car": ["https://circuitdigest.com/bluetooth-projects", "https://www.electronicshub.org/bluetooth-controlled-car-using-arduino/"],
    "IoT": ["https://www.iotforall.com/", "https://www.hackster.io/iot/projects"],
    "Capacitor": ["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
    "Robotics": ["https://www.robotshop.com/community/blog", "https://robohub.org/"],
    "Robotics Algorithms": ["https://towardsdatascience.com/tagged/robotics", "https://blogs.mathworks.com/robotics/"],
    "Circuit": ["https://www.electronicshub.org/", "https://circuitdigest.com/"],
    "Lead Acid Battery": ["https://batteryuniversity.com/article/bu-201-lead-acid-battery", "https://www.sciencedirect.com/topics/engineering/lead-acid-battery"],
    "Electrolytic Capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_7.html", "https://www.eevblog.com/"],
    "Ceramic Capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_3.html", "https://components101.com/articles/ceramic-capacitor-types-and-applications"],
    "Electrolytic vs. Ceramic Capacitors": ["https://www.electronics-notes.com/articles/electronic_components/capacitors/capacitor-types-ceramic-electrolytic-tantalum.php", "https://www.arrow.com/en/research-and-events/articles/electrolytic-vs-ceramic-capacitors"],
    "Node MCU": ["https://randomnerdtutorials.com/tag/nodemcu/", "https://maker.pro/esp8266/tutorials"],
    "Lithium Ion Battery": ["https://batteryuniversity.com/learn/article/lithium_based_batteries", "https://www.electronics-notes.com/articles/electronic_components/battery-technology/lithium-ion-li-ion.php"],
    "Line Follower Robot": ["https://www.robotshop.com/community/forum/t/line-follower-robots/27408", "https://www.instructables.com/howto/line+follower+robot/"],
    "Home Automation": ["https://www.home-assistant.io/blog/", "https://circuitdigest.com/home-automation-projects"],
    "ESP8266": ["https://randomnerdtutorials.com/esp8266-web-server/", "https://www.electronicwings.com/nodemcu/esp8266"],
    "capacitor":["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
     "arduino": ["https://blog.arduino.cc/", "https://www.instructables.com/howto/Arduino/"],
    "bluetooth controlled robot car": ["https://circuitdigest.com/bluetooth-projects", "https://www.electronicshub.org/bluetooth-controlled-car-using-arduino/"],
    "iot": ["https://www.iotforall.com/", "https://www.hackster.io/iot/projects"],
    "capacitor": ["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
    "robotics": ["https://www.robotshop.com/community/blog", "https://robohub.org/"],
    "robotics algorithms": ["https://towardsdatascience.com/tagged/robotics", "https://blogs.mathworks.com/robotics/"],
    "circuit": ["https://www.electronicshub.org/", "https://circuitdigest.com/"],
    "lead acid battery": ["https://batteryuniversity.com/article/bu-201-lead-acid-battery", "https://www.sciencedirect.com/topics/engineering/lead-acid-battery"],
    "electrolytic capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_7.html", "https://www.eevblog.com/"],
    "ceramic capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_3.html", "https://components101.com/articles/ceramic-capacitor-types-and-applications"],
    "electrolytic vs. ceramic capacitors": ["https://www.electronics-notes.com/articles/electronic_components/capacitors/capacitor-types-ceramic-electrolytic-tantalum.php", "https://www.arrow.com/en/research-and-events/articles/electrolytic-vs-ceramic-capacitors"],
    "node mcu": ["https://randomnerdtutorials.com/tag/nodemcu/", "https://maker.pro/esp8266/tutorials"],
    "lithium ion battery": ["https://batteryuniversity.com/learn/article/lithium_based_batteries", "https://www.electronics-notes.com/articles/electronic_components/battery-technology/lithium-ion-li-ion.php"],
    "line follower robot": ["https://www.robotshop.com/community/forum/t/line-follower-robots/27408", "https://www.instructables.com/howto/line+follower+robot/"],
    "home automation": ["https://www.home-assistant.io/blog/", "https://circuitdigest.com/home-automation-projects"],
    "esp8266": ["https://randomnerdtutorials.com/esp8266-web-server/", "https://www.electronicwings.com/nodemcu/esp8266"],
    "capacitor":["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
     "bluetooth controlled robot car": ["https://circuitdigest.com/bluetooth-projects", "https://www.electronicshub.org/bluetooth-controlled-car-using-arduino/"],
    "iot": ["https://www.iotforall.com/", "https://www.hackster.io/iot/projects"],
    "capacitors": ["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],
    "robo": ["https://www.robotshop.com/community/blog", "https://robohub.org/"],
    "robo algo": ["https://towardsdatascience.com/tagged/robotics", "https://blogs.mathworks.com/robotics/"],
    "circuits": ["https://www.electronicshub.org/", "https://circuitdigest.com/"],
    "lead  battery": ["https://batteryuniversity.com/article/bu-201-lead-acid-battery", "https://www.sciencedirect.com/topics/engineering/lead-acid-battery"],
    "electric capacitors": ["https://www.electronics-tutorials.ws/capacitor/cap_7.html", "https://www.eevblog.com/"],
    "ceramic": ["https://www.electronics-tutorials.ws/capacitor/cap_3.html", "https://components101.com/articles/ceramic-capacitor-types-and-applications"],
    "electrolytic vs. ceramic": ["https://www.electronics-notes.com/articles/electronic_components/capacitors/capacitor-types-ceramic-electrolytic-tantalum.php", "https://www.arrow.com/en/research-and-events/articles/electrolytic-vs-ceramic-capacitors"],
    "nodemcu": ["https://randomnerdtutorials.com/tag/nodemcu/", "https://maker.pro/esp8266/tutorials"],
    "lithium battery": ["https://batteryuniversity.com/learn/article/lithium_based_batteries", "https://www.electronics-notes.com/articles/electronic_components/battery-technology/lithium-ion-li-ion.php"],
    "line follow robot": ["https://www.robotshop.com/community/forum/t/line-follower-robots/27408", "https://www.instructables.com/howto/line+follower+robot/"],
    "automatic home": ["https://www.home-assistant.io/blog/", "https://circuitdigest.com/home-automation-projects"],
    "chip": ["https://randomnerdtutorials.com/esp8266-web-server/", "https://www.electronicwings.com/nodemcu/esp8266"],
    "capacitor types":["https://www.allaboutcircuits.com/textbook/direct-current/chpt-13/capacitors/", "https://www.electronics-tutorials.ws/capacitor/cap_1.html"],

}


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = generate_password_hash(request.form['password'])
            
            if User.query.filter_by(email=email).first():
                logger.warning(f"Registration attempt with existing email: {email}")
                return "User with this email already exists"
            
            new_user = User(username=username, email=email, password=password)
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"New user registered: {username}")
            return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Error in registration: {str(e)}")
        return "An error occurred during registration. Please try again."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                logger.info(f"User logged in: {email}")
                return redirect(url_for('ghat'))
            
            logger.warning(f"Failed login attempt for email: {email}")
            return "Invalid credentials. Please try again."
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return "An error occurred during login. Please try again."
    return render_template('login.html')

@app.route('/ghat')
def ghat():
    if 'user_id' in session:
        return render_template('ghat.html')
    return redirect(url_for('login'))

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    try:
        if request.method == 'POST':
            query = request.form.get('query', '').strip()
            if not query:
                return jsonify({'error': 'Query cannot be empty'}), 400
                
            response_data = process_search_query(query, user_id)
            return jsonify(response_data)
            
        else:
            query = request.args.get('query', '')
            chat_history = db.session.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.timestamp.desc()).all()
            
            if query:
                response_data = process_search_query(query, user_id)
                return render_template('chat.html', 
                                    chat_history=chat_history,
                                    current_query=query,
                                    current_response=response_data)
            
            return render_template('chat.html', chat_history=chat_history)
            
    except Exception as e:
        logger.error(f"Error in chat route: {str(e)}")
        if request.method == 'POST':
            return jsonify({'error': 'An error occurred processing your request'}), 500
        return render_template('chat.html', error="An error occurred. Please try again.")

def process_search_query(query, user_id):
    try:
        response_data = {"pdf_embed_url": "", "embedded_website": "", "ai_response": ""}
        
        # Check for PDF
        pdf_path = os.path.join(app.config['PDF_FOLDER'], f"{query}.pdf")
        if os.path.exists(pdf_path):
            response_data["pdf_embed_url"] = url_for('serve_pdf', filename=f"{query}.pdf")
        
        # Check for embedded website
        query_lower = query.lower()
        if query_lower in keyword_links:
            response_data["embedded_website"] = keyword_links[query_lower][0]
        
        # Get AI response
        if query:
            headers = {
                "Content-Type": "application/json",
                "api-key": openai.api_key
            }
            json_body = {
                "messages": [
                    {"role": "system", "content": "You are an AI assistant that helps people find information."},
                    {"role": "user", "content": query}
                ],
                "max_tokens": 800,
                "temperature": 0.7,
                "top_p": 0.95,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
            try:
                azure_response = requests.post(
                    f"{openai.api_base}openai/deployments/{DEPLOYMENT_NAME}/chat/completions?api-version={openai.api_version}",
                    headers=headers,
                    json=json_body
                )
                if azure_response.status_code == 200:
                    response_content = azure_response.json()
                    clean_text = clean_response(response_content['choices'][0]['message']['content'])
                    response_data["ai_response"] = clean_text
                else:
                    logger.error(f"OpenAI API error: {azure_response.status_code}")
                    response_data["ai_response"] = f"Error: {azure_response.status_code}"
            except Exception as e:
                logger.error(f"Error generating OpenAI response: {str(e)}")
                response_data["ai_response"] = "There was an error generating the response. Please try again later."

        # Store in chat history
        new_chat = Chat(user_id=user_id, query=query, response=response_data["ai_response"])
        db.session.add(new_chat)
        db.session.commit()
        
        return response_data
    except Exception as e:
        logger.error(f"Error in process_search_query: {str(e)}")
        return {"pdf_embed_url": "", "embedded_website": "", "ai_response": "An error occurred processing your request."}

@app.route('/pdfs/<filename>')
def serve_pdf(filename):
    try:
        return send_from_directory('data', filename)
    except FileNotFoundError:
        logger.warning(f"PDF not found: {filename}")
        return "PDF not found.", 404

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    logger.info("User logged out")
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise
    
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
