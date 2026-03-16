from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime, timedelta
import json
import base64
import cv2
import numpy as np
from io import BytesIO
import logging
import time

from models import db, User, TestResult, HealthCondition
from utils.face_analysis1 import EnhancedFaceAnalyzer
from utils.report_generator import generate_pdf_report

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'neuroface-secret-key-2024')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Add custom Jinja2 filters
@app.template_filter('fromjson')
def fromjson_filter(value):
    """Convert JSON string to Python object"""
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except:
        return []

@app.template_filter('tojson')
def tojson_filter(value):
    """Convert Python object to JSON string"""
    try:
        return json.dumps(value)
    except:
        return '[]'

# Global analyzer instance per session
face_analyzers = {}

def get_analyzer(session_id):
    """Get or create analyzer for session"""
    if session_id not in face_analyzers:
        # Make sure this matches your actual filename
        from utils.face_analysis1 import EnhancedFaceAnalyzer
        face_analyzers[session_id] = EnhancedFaceAnalyzer()
    return face_analyzers[session_id]

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        age = request.form.get('age', 0, type=int)
        gender = request.form.get('gender', 'prefer_not_to_say')
        
        # Validation
        errors = []
        if len(username) < 3:
            errors.append('Username must be at least 3 characters long')
        if not email or '@' not in email:
            errors.append('Please enter a valid email address')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        if User.query.filter_by(username=username).first():
            errors.append('Username already taken')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(
            username=username,
            email=email,
            password=hashed_password,
            age=age if age > 0 else None,
            gender=gender
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Registration successful! Welcome to NeuroFace Analyzer.', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {e}")
            flash('An error occurred during registration. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = 'remember' in request.form
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # Clean up analyzer
    session_id = session.get('session_id')
    if session_id and session_id in face_analyzers:
        del face_analyzers[session_id]
    
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    name = request.form.get('name')
    age = request.form.get('age')

    current_user.name = name
    current_user.age = age

    db.session.commit()

    flash('Profile updated successfully!', 'success')
    return redirect(url_for('profile'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_results = TestResult.query.filter_by(user_id=current_user.id)\
        .order_by(TestResult.test_date.desc()).limit(10).all()
    
    # Calculate statistics
    total_tests = len(user_results)
    avg_blink_rate = 0
    common_conditions = []
    
    if total_tests > 0:
        avg_blink_rate = sum(r.blink_rate for r in user_results) / total_tests
        
        # Get most common conditions
        all_conditions = []
        for result in user_results:
            if result.conditions:
                conditions = json.loads(result.conditions)
                all_conditions.extend(conditions)
        
        from collections import Counter
        condition_counter = Counter(all_conditions)
        common_conditions = condition_counter.most_common(3)
    
    return render_template('dashboard.html', 
                         results=user_results,
                         total_tests=total_tests,
                         avg_blink_rate=avg_blink_rate,
                         common_conditions=common_conditions)

@app.route('/start_test')
@login_required
def start_test():
    # Create session ID for this test
    session_id = f"{current_user.id}_{int(time.time())}"
    session['session_id'] = session_id
    
    # Initialize analyzer
    analyzer = get_analyzer(session_id)
    analyzer.start_test_session()
    analyzer.test_start_time = time.time()
    
    return render_template('test.html', session_id=session_id)

@app.route('/analyze_frame', methods=['POST'])
@login_required
def analyze_frame_endpoint():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Get session ID
        session_id = data.get('session_id', session.get('session_id'))
        if not session_id:
            return jsonify({'error': 'No active test session'}), 400
        
        # Get analyzer
        analyzer = get_analyzer(session_id)
        
        # Extract image data
        image_data = data['image'].split(',')[1]
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Invalid image data'}), 400
        
        # Get settings
        draw_mesh = data.get('draw_mesh', True)
        
        # Analyze the frame
        analysis = analyzer.process_frame(frame, draw_mesh)
        
        # Ensure JSON serializability
        analysis['blink_detected'] = bool(analysis['blink_detected'])
        analysis['blink_count'] = int(analysis['blink_count'])
        analysis['ear'] = float(analysis['ear'])
        analysis['ear_asymmetry'] = float(analysis['ear_asymmetry'])
        analysis['has_face'] = bool(analysis['has_face'])
        analysis['facial_asymmetry'] = float(analysis['facial_asymmetry'])
        
        # Convert expression values to ints
        for key in analysis['expressions']:
            analysis['expressions'][key] = int(analysis['expressions'][key])
        
        # Convert action unit values to floats
        for key in analysis['action_units']:
            analysis['action_units'][key] = float(analysis['action_units'][key])
        
        # Convert health metrics
        for key in analysis['health_metrics']:
            analysis['health_metrics'][key] = float(analysis['health_metrics'][key])
        
        # Convert annotated frame to base64 if exists
        if analysis.get('frame_annotated') is not None:
            _, buffer = cv2.imencode('.jpg', analysis['frame_annotated'])
            annotated_base64 = base64.b64encode(buffer).decode('utf-8')
            analysis['annotated_image'] = f"data:image/jpeg;base64,{annotated_base64}"
            del analysis['frame_annotated']
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error analyzing frame: {e}")
        return jsonify({'error': str(e), 'has_face': False}), 500

@app.route('/complete_test', methods=['POST'])
@login_required
def complete_test():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = data.get('session_id', session.get('session_id'))
        if not session_id:
            return jsonify({'error': 'No active test session'}), 400
        
        # Get analyzer and final analysis
        analyzer = get_analyzer(session_id)
        
        # Calculate test duration
        test_duration = data.get('test_duration', 60)  # Default 60 seconds
        duration_minutes = test_duration / 60.0
        
        # Get comprehensive analysis
        analysis = analyzer.get_comprehensive_analysis(duration_minutes)
        
        # Extract single disease prediction
        primary_condition = analysis.get('primary_condition', 'No specific condition detected')
        condition_confidence = analysis.get('condition_confidence', 0)
        
        # Create conditions list (single condition for display)
        conditions = [primary_condition] if primary_condition != 'No specific condition detected' else []
        
        # Create confidence scores dict
        confidence_scores = {primary_condition: condition_confidence} if primary_condition != 'No specific condition detected' else {}
        
        # Save to database
        new_result = TestResult(
            user_id=current_user.id,
            blink_count=analysis['blink_count'],
            blink_rate=analysis['blink_rate'],
            micro_expressions=json.dumps(analysis['avg_expressions']),
            conditions=json.dumps(conditions),
            confidence_scores=json.dumps(confidence_scores),
            recommendations=json.dumps(analysis['recommendations']),
            facial_asymmetry=analysis.get('facial_asymmetry', 0.0),
            expression_variability=analysis.get('expression_variability', 0.0),
            test_duration=test_duration,
            test_date=datetime.utcnow()
        )
        
        db.session.add(new_result)
        db.session.commit()
        
        # Save single health condition
        if primary_condition != 'No specific condition detected':
            health_condition = HealthCondition(
                test_result_id=new_result.id,
                condition_name=primary_condition,
                confidence_score=condition_confidence,
                detected_at=datetime.utcnow()
            )
            db.session.add(health_condition)
            db.session.commit()
        
        # Clean up analyzer
        if session_id in face_analyzers:
            del face_analyzers[session_id]
        
        return jsonify({
            'success': True,
            'result_id': new_result.id,
            'blink_count': analysis['blink_count'],
            'blink_rate': analysis['blink_rate'],
            'primary_condition': primary_condition,
            'condition_confidence': condition_confidence,
            'recommendations': analysis['recommendations']
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing test: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@app.route('/results/<int:result_id>')
@login_required
def results(result_id):
    result = TestResult.query.get_or_404(result_id)
    
    # Check ownership
    if result.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Parse JSON data
    micro_expressions = json.loads(result.micro_expressions) if result.micro_expressions else {}
    conditions = json.loads(result.conditions) if result.conditions else []
    confidence_scores = json.loads(result.confidence_scores) if result.confidence_scores else {}
    recommendations = json.loads(result.recommendations) if result.recommendations else []
    
    # Get associated health conditions
    health_conditions = HealthCondition.query.filter_by(test_result_id=result.id).all()
    
    return render_template('results.html',
                         result=result,
                         micro_expressions=micro_expressions,
                         conditions=conditions,
                         confidence_scores=confidence_scores,
                         recommendations=recommendations,
                         health_conditions=health_conditions)

@app.route('/download_report/<int:result_id>')
@login_required
def download_report(result_id):
    result = TestResult.query.get_or_404(result_id)
    
    # Check ownership
    if result.user_id != current_user.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('dashboard'))
    
    user = User.query.get(result.user_id)
    micro_expressions = json.loads(result.micro_expressions) if result.micro_expressions else {}
    conditions = json.loads(result.conditions) if result.conditions else []
    confidence_scores = json.loads(result.confidence_scores) if result.confidence_scores else {}
    recommendations = json.loads(result.recommendations) if result.recommendations else []
    
    try:
        pdf_data = generate_pdf_report(
            user, result, micro_expressions, 
            conditions, confidence_scores, recommendations
        )
        
        filename = f"neuroface_health_report_{user.username}_{result.test_date.strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        flash('Error generating report. Please try again.', 'danger')
        return redirect(url_for('results', result_id=result_id))

@app.route('/profile')
@login_required
def profile():
    user_results = TestResult.query.filter_by(user_id=current_user.id).all()
    total_tests = len(user_results)
    
    # Calculate account age in days
    account_age = (datetime.utcnow() - current_user.created_at).days
    
    # Get health insights
    health_conditions = []
    if user_results:
        latest_result = user_results[0]
        if latest_result.conditions:
            health_conditions = json.loads(latest_result.conditions)
    
    return render_template('profile.html',
                         total_tests=total_tests,
                         account_age=account_age,
                         health_conditions=health_conditions[:3])

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.route('/api/health_conditions')
@login_required
def get_health_conditions():
    """Get information about detectable health conditions"""
    conditions_info = {
        'dry_eye_syndrome': {
            'name': 'Dry Eye Syndrome / Blepharitis',
            'indicators': ['Reduced blinking (<8 blinks/min)', 'Eye irritation', 'Reduced tear production'],
            'recommendations': ['Artificial tears', 'Warm compresses', 'Ophthalmology consultation']
        },
        'stress_anxiety': {
            'name': 'Stress & Anxiety Disorders',
            'indicators': ['Increased blinking (>25 blinks/min)', 'Facial tension', 'Micro-expressions of fear'],
            'recommendations': ['Stress management', 'Mindfulness meditation', 'Therapy']
        },
        'parkinsons': {
            'name': "Parkinson's Disease Indicators",
            'indicators': ['Reduced facial expressivity', 'Mask-like facies', 'Reduced blinking'],
            'recommendations': ['Neurology consultation', 'Facial exercises', 'Medication management']
        },
        'bells_palsy': {
            'name': "Bell's Palsy / Stroke Indicators",
            'indicators': ['Facial asymmetry', 'Drooping on one side', 'Difficulty closing eye'],
            'recommendations': ['Immediate medical attention', 'Neurology consultation', 'Physical therapy']
        },
        'depression': {
            'name': 'Depression Indicators',
            'indicators': ['Sad micro-expressions', 'Reduced emotional variability', 'Flat affect'],
            'recommendations': ['Mental health evaluation', 'Therapy', 'Support groups']
        },
        'hyperthyroidism': {
            'name': 'Hyperthyroidism Indicators',
            'indicators': ['Staring appearance', 'Reduced blinking', 'Lid lag'],
            'recommendations': ['Thyroid function tests', 'Endocrinology consultation', 'Medication']
        },
        'myasthenia_gravis': {
            'name': 'Myasthenia Gravis Indicators',
            'indicators': ['Ptosis (drooping eyelids)', 'Weak eye closure', 'Fatigable weakness'],
            'recommendations': ['Neurology consultation', 'Acetylcholine receptor tests', 'Treatment']
        },
        'als': {
            'name': 'ALS / Motor Neuron Disease Indicators',
            'indicators': ['Progressive weakness', 'Reduced facial movements', 'Difficulty speaking'],
            'recommendations': ['Neurology specialist', 'Comprehensive evaluation', 'Supportive care']
        }
    }
    
    return jsonify(conditions_info)

if __name__ == '__main__':
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)