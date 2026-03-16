# import cv2
# import mediapipe as mp
# import numpy as np
# from collections import deque
# import math
# import pickle
# from sklearn.ensemble import RandomForestClassifier
# import joblib
# import os

# class EnhancedFaceAnalyzer:
#     def __init__(self):
#         # Initialize MediaPipe Face Mesh
#         self.face_mesh = mp.solutions.face_mesh.FaceMesh(
#             max_num_faces=1,
#             refine_landmarks=True,
#             min_detection_confidence=0.7,
#             min_tracking_confidence=0.7,
#             static_image_mode=False
#         )
        
#         # Eye landmark indices (more precise)
#         self.LEFT_EYE_INDICES = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
#         self.RIGHT_EYE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
        
#         # Facial Action Unit landmarks (for micro-expressions)
#         self.FACIAL_ACTION_UNITS = {
#             # AU1 - Inner Brow Raiser
#             'au1_left': [336, 296, 334],
#             'au1_right': [107, 66, 105],
            
#             # AU2 - Outer Brow Raiser
#             'au2_left': [334, 293, 300],
#             'au2_right': [105, 63, 70],
            
#             # AU4 - Brow Lowerer
#             'au4_left': [285, 295, 282],
#             'au4_right': [55, 65, 52],
            
#             # AU5 - Upper Lid Raiser
#             'au5_left': [386, 374, 263],
#             'au5_right': [159, 145, 133],
            
#             # AU6 - Cheek Raiser
#             'au6_left': [412, 432, 434],
#             'au6_right': [187, 207, 209],
            
#             # AU7 - Lid Tightener
#             'au7_left': [386, 374, 362],
#             'au7_right': [159, 145, 33],
            
#             # AU9 - Nose Wrinkler
#             'au9': [168, 197, 195, 5, 4],
            
#             # AU12 - Lip Corner Puller (Smile)
#             'au12_left': [61, 185, 40],
#             'au12_right': [291, 409, 270],
            
#             # AU15 - Lip Corner Depressor (Sad)
#             'au15_left': [61, 88, 78],
#             'au15_right': [291, 317, 308],
            
#             # AU17 - Chin Raiser
#             'au17': [152, 176, 148, 149],
            
#             # AU20 - Lip Stretcher
#             'au20_left': [61, 76, 62],
#             'au20_right': [291, 306, 292],
            
#             # AU23 - Lip Tightener
#             'au23': [78, 95, 88, 178, 87, 14],
            
#             # AU25 - Lips Part
#             'au25': [13, 14, 78, 308],
            
#             # AU26 - Jaw Drop
#             'au26': [17, 84, 181, 91]
#         }
        
#         # Blink detection parameters
#         self.BLINK_THRESHOLD = 0.22  # Eye Aspect Ratio threshold
#         self.BLINK_CONSECUTIVE_FRAMES = 2  # Minimum frames for blink
#         self.blink_counter = 0
#         self.eye_closed_frames = 0
#         self.ear_history = deque(maxlen=10)
        
#         # Micro-expression tracking
#         self.micro_expression_history = deque(maxlen=30)
#         self.action_unit_history = deque(maxlen=20)
        
#         # Health metrics
#         self.blink_rate_per_minute = 0
#         self.expression_intensity = {
#             'neutral': 100,
#             'happy': 0,
#             'sad': 0,
#             'angry': 0,
#             'surprised': 0,
#             'fearful': 0,
#             'disgusted': 0,
#             'contempt': 0
#         }
        
#         # Disease prediction model (placeholder - will be trained)
#         self.disease_model = self.load_or_create_disease_model()
        
#         # Performance tracking
#         self.frame_count = 0
#         self.test_start_time = None
        
#     def load_or_create_disease_model(self):
#         """Load or create disease prediction model"""
#         model_path = "models/disease_predictor.pkl"
        
#         if os.path.exists(model_path):
#             try:
#                 return joblib.load(model_path)
#             except:
#                 pass
        
#         # Create a basic model structure (in production, this would be trained)
#         # This is a placeholder model structure
#         model = {
#             'blink_rate_ranges': {
#                 'low': (0, 8),      # Dry Eye Syndrome
#                 'normal': (8, 20),   # Healthy
#                 'high': (20, 100)    # Stress/Anxiety
#             },
#             'expression_patterns': {
#                 'depression': ['sad', 'neutral_high'],
#                 'anxiety': ['fearful', 'surprised', 'angry'],
#                 'parkinsons': ['reduced_blinking', 'masked_facials'],
#                 'bell_palsy': ['asymmetrical_expressions'],
#                 'stroke': ['asymmetrical_expressions', 'drooping'],
#                 'hyperthyroidism': ['staring', 'reduced_blinking'],
#                 'myasthenia_gravis': ['ptosis', 'weak_expressions'],
#                 'als': ['weak_expressions', 'reduced_blinking']
#             }
#         }
#         return model
    
#     def calculate_eye_aspect_ratio(self, landmarks, eye_indices):
#         """Calculate precise Eye Aspect Ratio"""
#         # Extract eye landmarks
#         eye_points = np.array([[landmarks[i].x, landmarks[i].y] for i in eye_indices])
        
#         # Compute vertical distances
#         vertical1 = np.linalg.norm(eye_points[1] - eye_points[7])
#         vertical2 = np.linalg.norm(eye_points[2] - eye_points[6])
#         vertical3 = np.linalg.norm(eye_points[3] - eye_points[5])
        
#         # Compute horizontal distance
#         horizontal = np.linalg.norm(eye_points[0] - eye_points[4])
        
#         # Calculate EAR
#         ear = (vertical1 + vertical2 + vertical3) / (3.0 * horizontal)
#         return float(ear)
    
#     def detect_blink(self, landmarks):
#         """Advanced blink detection with adaptive threshold"""
#         left_ear = self.calculate_eye_aspect_ratio(landmarks, self.LEFT_EYE_INDICES)
#         right_ear = self.calculate_eye_aspect_ratio(landmarks, self.RIGHT_EYE_INDICES)
        
#         ear = (left_ear + right_ear) / 2.0
#         self.ear_history.append(ear)
        
#         # Adaptive threshold based on history
#         if len(self.ear_history) > 5:
#             avg_ear = np.mean(self.ear_history)
#             adaptive_threshold = avg_ear * 0.7  # 30% drop indicates blink
#         else:
#             adaptive_threshold = self.BLINK_THRESHOLD
        
#         blink_detected = False
        
#         if ear < adaptive_threshold:
#             self.eye_closed_frames += 1
#         else:
#             if self.eye_closed_frames >= self.BLINK_CONSECUTIVE_FRAMES:
#                 self.blink_counter += 1
#                 blink_detected = True
#             self.eye_closed_frames = 0
        
#         # Calculate blink asymmetry (potential neurological indicator)
#         ear_asymmetry = abs(left_ear - right_ear)
        
#         return bool(blink_detected), float(ear), float(ear_asymmetry)
    
#     def calculate_action_unit_intensity(self, landmarks, au_points):
#         """Calculate intensity of Facial Action Units"""
#         if isinstance(au_points[0], list):
#             # Multiple points for complex AUs
#             intensities = []
#             for point_group in au_points:
#                 if len(point_group) >= 3:
#                     # Calculate angle or distance-based intensity
#                     p1 = landmarks[point_group[0]]
#                     p2 = landmarks[point_group[1]]
#                     p3 = landmarks[point_group[2]]
                    
#                     # Calculate angle between vectors
#                     v1 = np.array([p2.x - p1.x, p2.y - p1.y])
#                     v2 = np.array([p3.x - p1.x, p3.y - p1.y])
                    
#                     angle = np.degrees(np.arccos(
#                         np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
#                     ))
#                     intensities.append(angle)
#             return np.mean(intensities) if intensities else 0
#         else:
#             # Simple distance-based intensity
#             if len(au_points) >= 2:
#                 p1 = landmarks[au_points[0]]
#                 p2 = landmarks[au_points[1]]
#                 distance = math.sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
#                 return float(distance * 100)  # Scale for intensity
#         return 0.0
    
#     def analyze_micro_expressions(self, landmarks):
#         """Analyze micro-expressions using Facial Action Coding System (FACS)"""
#         action_units = {}
        
#         # Calculate each Action Unit intensity
#         for au_name, au_points in self.FACIAL_ACTION_UNITS.items():
#             intensity = self.calculate_action_unit_intensity(landmarks, au_points)
#             action_units[au_name] = float(intensity)
        
#         # Map Action Units to emotions
#         emotions = self.map_action_units_to_emotions(action_units)
        
#         # Store in history
#         self.action_unit_history.append(action_units)
#         self.micro_expression_history.append(emotions)
        
#         return emotions, action_units
    
#     def map_action_units_to_emotions(self, action_units):
#         """Map FACS Action Units to specific emotions"""
#         emotions = {
#             'neutral': 100,
#             'happy': 0,
#             'sad': 0,
#             'angry': 0,
#             'surprised': 0,
#             'fearful': 0,
#             'disgusted': 0,
#             'contempt': 0
#         }
        
#         # Happiness (AU6 + AU12)
#         if action_units.get('au6_left', 0) > 15 or action_units.get('au6_right', 0) > 15:
#             if action_units.get('au12_left', 0) > 20 or action_units.get('au12_right', 0) > 20:
#                 emotions['happy'] = min(100, int(
#                     (action_units.get('au6_left', 0) + action_units.get('au6_right', 0) +
#                      action_units.get('au12_left', 0) + action_units.get('au12_right', 0)) / 4
#                 ))
        
#         # Sadness (AU1 + AU4 + AU15)
#         if action_units.get('au1_left', 0) > 10 or action_units.get('au1_right', 0) > 10:
#             if action_units.get('au15_left', 0) > 15 or action_units.get('au15_right', 0) > 15:
#                 emotions['sad'] = min(100, int(
#                     (action_units.get('au1_left', 0) + action_units.get('au1_right', 0) +
#                      action_units.get('au15_left', 0) + action_units.get('au15_right', 0)) / 4
#                 ))
        
#         # Anger (AU4 + AU5 + AU7 + AU23)
#         if action_units.get('au4_left', 0) > 20 or action_units.get('au4_right', 0) > 20:
#             if action_units.get('au23', 0) > 15:
#                 emotions['angry'] = min(100, int(
#                     (action_units.get('au4_left', 0) + action_units.get('au4_right', 0) +
#                      action_units.get('au23', 0)) / 3
#                 ))
        
#         # Surprise (AU1 + AU2 + AU5 + AU26)
#         if (action_units.get('au1_left', 0) > 15 or action_units.get('au1_right', 0) > 15):
#             if action_units.get('au2_left', 0) > 15 or action_units.get('au2_right', 0) > 15:
#                 if action_units.get('au26', 0) > 10:
#                     emotions['surprised'] = min(100, int(
#                         (action_units.get('au1_left', 0) + action_units.get('au1_right', 0) +
#                          action_units.get('au2_left', 0) + action_units.get('au2_right', 0) +
#                          action_units.get('au26', 0)) / 5
#                     ))
        
#         # Fear (AU1 + AU2 + AU4 + AU5 + AU7 + AU20 + AU26)
#         fear_indicators = [
#             action_units.get('au1_left', 0), action_units.get('au1_right', 0),
#             action_units.get('au4_left', 0), action_units.get('au4_right', 0),
#             action_units.get('au20_left', 0), action_units.get('au20_right', 0)
#         ]
#         if any(indicator > 15 for indicator in fear_indicators):
#             emotions['fearful'] = min(100, int(np.mean([i for i in fear_indicators if i > 0])))
        
#         # Disgust (AU9 + AU15 + AU16)
#         if action_units.get('au9', 0) > 20:
#             emotions['disgusted'] = min(100, int(action_units.get('au9', 0)))
        
#         # Contempt (AU12 asymmetrical + AU14)
#         if abs(action_units.get('au12_left', 0) - action_units.get('au12_right', 0)) > 15:
#             emotions['contempt'] = min(100, int(
#                 abs(action_units.get('au12_left', 0) - action_units.get('au12_right', 0))
#             ))
        
#         # Normalize emotions (sum to 100)
#         total_emotion = sum(emotions.values())
#         if total_emotion > 100:
#             scale = 100 / total_emotion
#             for emotion in emotions:
#                 emotions[emotion] = int(emotions[emotion] * scale)
#         elif total_emotion < 100:
#             emotions['neutral'] = 100 - sum([v for k, v in emotions.items() if k != 'neutral'])
        
#         return emotions
    
#     def predict_health_conditions(self, blink_rate, facial_asymmetry, expression_patterns):
#         """Predict potential health conditions based on facial metrics"""
#         conditions = []
#         confidence_scores = {}
        
#         # 1. Dry Eye Syndrome / Blepharitis
#         if blink_rate < 8:
#             conditions.append("Dry Eye Syndrome / Blepharitis")
#             confidence = min(100, int((8 - blink_rate) * 10))
#             confidence_scores["Dry Eye Syndrome / Blepharitis"] = confidence
        
#         # 2. Stress & Anxiety Disorders
#         elif blink_rate > 25:
#             conditions.append("Stress & Anxiety Disorders")
#             confidence = min(100, int((blink_rate - 20) * 3))
#             confidence_scores["Stress & Anxiety Disorders"] = confidence
        
#         # 3. Neurological Disorders (Parkinson's, Bell's Palsy)
#         if facial_asymmetry > 0.05:  # Significant facial asymmetry
#             if expression_patterns.get('reduced_expressivity', False):
#                 conditions.append("Parkinson's Disease Indicators")
#                 confidence = min(100, int(facial_asymmetry * 200))
#                 confidence_scores["Parkinson's Disease Indicators"] = confidence
#             else:
#                 conditions.append("Bell's Palsy / Stroke Indicators")
#                 confidence = min(100, int(facial_asymmetry * 150))
#                 confidence_scores["Bell's Palsy / Stroke Indicators"] = confidence
        
#         # 4. Depression (from facial expressions)
#         if expression_patterns.get('sad', 0) > 40 and expression_patterns.get('neutral', 0) > 50:
#             conditions.append("Depression Indicators")
#             confidence = min(100, int((expression_patterns['sad'] + expression_patterns['neutral']) / 2))
#             confidence_scores["Depression Indicators"] = confidence
        
#         # 5. Hyperthyroidism (staring, reduced blinking)
#         if blink_rate < 10 and expression_patterns.get('surprised', 0) > 30:
#             conditions.append("Hyperthyroidism Indicators")
#             confidence = min(100, int((30 - blink_rate) * 3 + expression_patterns['surprised']))
#             confidence_scores["Hyperthyroidism Indicators"] = confidence
        
#         # 6. Myasthenia Gravis (ptosis, weak expressions)
#         if expression_patterns.get('weak_eye_closure', False):
#             conditions.append("Myasthenia Gravis Indicators")
#             confidence = 60
#             confidence_scores["Myasthenia Gravis Indicators"] = confidence
        
#         # 7. ALS (progressive weakness)
#         if expression_patterns.get('reduced_expressivity', False) and blink_rate < 15:
#             conditions.append("ALS / Motor Neuron Disease Indicators")
#             confidence = 50
#             confidence_scores["ALS / Motor Neuron Disease Indicators"] = confidence
        
#         # 8. Chronic Fatigue Syndrome
#         if blink_rate > 20 and expression_patterns.get('neutral', 0) > 70:
#             conditions.append("Chronic Fatigue Syndrome Indicators")
#             confidence = min(100, int((blink_rate - 15) * 2 + expression_patterns['neutral'] / 2))
#             confidence_scores["Chronic Fatigue Syndrome Indicators"] = confidence
        
#         # Sort by confidence
#         conditions.sort(key=lambda x: confidence_scores.get(x, 0), reverse=True)
        
#         return conditions, confidence_scores
    
#     def draw_advanced_face_mesh(self, frame, landmarks, draw_mesh=True):
#         """Draw advanced face mesh with different colors for different regions"""
#         h, w, _ = frame.shape
        
#         if draw_mesh:
#             # Draw eye regions (green)
#             for idx in self.LEFT_EYE_INDICES + self.RIGHT_EYE_INDICES:
#                 point = landmarks[idx]
#                 x, y = int(point.x * w), int(point.y * h)
#                 cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
            
#             # Draw mouth region (red)
#             mouth_indices = [13, 14, 78, 308, 61, 291, 402, 318]
#             for idx in mouth_indices:
#                 point = landmarks[idx]
#                 x, y = int(point.x * w), int(point.y * h)
#                 cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)
            
#             # Draw eyebrow regions (blue)
#             eyebrow_indices = [55, 65, 52, 53, 46, 285, 295, 282, 283, 276]
#             for idx in eyebrow_indices:
#                 point = landmarks[idx]
#                 x, y = int(point.x * w), int(point.y * h)
#                 cv2.circle(frame, (x, y), 2, (255, 0, 0), -1)
            
#             # Draw connections
#             self.draw_face_connections(frame, landmarks, w, h)
        
#         return frame
    
#     def draw_face_connections(self, frame, landmarks, w, h):
#         """Draw connections between facial landmarks"""
#         # Eye connections
#         left_eye_points = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) 
#                           for i in self.LEFT_EYE_INDICES]
#         right_eye_points = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) 
#                            for i in self.RIGHT_EYE_INDICES]
        
#         for points in [left_eye_points, right_eye_points]:
#             for i in range(len(points) - 1):
#                 cv2.line(frame, points[i], points[i + 1], (0, 255, 255), 1)
#             cv2.line(frame, points[-1], points[0], (0, 255, 255), 1)
    
#     def calculate_facial_asymmetry(self, landmarks):
#         """Calculate facial asymmetry score (0-1 where 0 is perfectly symmetrical)"""
#         # Key symmetrical points
#         symmetrical_pairs = [
#             (33, 263),   # Outer eye corners
#             (130, 359),  # Cheekbones
#             (61, 291),   # Mouth corners
#             (55, 285),   # Eyebrow outer
#             (65, 295),   # Eyebrow inner
#         ]
        
#         asymmetries = []
#         for left_idx, right_idx in symmetrical_pairs:
#             left_point = landmarks[left_idx]
#             right_point = landmarks[right_idx]
            
#             # Horizontal asymmetry
#             horizontal_diff = abs((1 - left_point.x) - right_point.x)  # Account for mirror
            
#             # Vertical asymmetry
#             vertical_diff = abs(left_point.y - right_point.y)
            
#             total_diff = math.sqrt(horizontal_diff**2 + vertical_diff**2)
#             asymmetries.append(total_diff)
        
#         return float(np.mean(asymmetries)) if asymmetries else 0.0
    
#     def process_frame(self, frame, draw_mesh=True):
#         """Process a single frame for comprehensive analysis"""
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = self.face_mesh.process(rgb_frame)
        
#         # Initialize with default values
#         analysis = {
#             'blink_detected': False,
#             'blink_count': int(self.blink_counter),
#             'ear': 0.3,
#             'ear_asymmetry': 0.0,
#             'expressions': self.expression_intensity.copy(),
#             'action_units': {},
#             'has_face': False,
#             'facial_asymmetry': 0.0,
#             'health_metrics': {
#                 'blink_rate': 0,
#                 'expression_variability': 0,
#                 'facial_symmetry': 1.0
#             },
#             'frame_annotated': None
#         }
        
#         if results.multi_face_landmarks:
#             analysis['has_face'] = True
#             landmarks = results.multi_face_landmarks[0].landmark
            
#             # Detect blink
#             blink_detected, ear, ear_asymmetry = self.detect_blink(landmarks)
#             analysis['blink_detected'] = bool(blink_detected)
#             analysis['ear'] = float(ear)
#             analysis['ear_asymmetry'] = float(ear_asymmetry)
            
#             # Calculate facial asymmetry
#             facial_asymmetry = self.calculate_facial_asymmetry(landmarks)
#             analysis['facial_asymmetry'] = float(facial_asymmetry)
#             analysis['health_metrics']['facial_symmetry'] = float(1.0 - facial_asymmetry)
            
#             # Analyze micro-expressions
#             try:
#                 emotions, action_units = self.analyze_micro_expressions(landmarks)
#                 analysis['expressions'] = emotions
#                 analysis['action_units'] = action_units
#             except Exception as e:
#                 print(f"Expression analysis error: {e}")
#                 # Use default expressions
            
#             # Calculate expression variability
#             if len(self.micro_expression_history) > 1:
#                 variability = self.calculate_expression_variability()
#                 analysis['health_metrics']['expression_variability'] = float(variability)
            
#             # Calculate blink rate if test has started
#             if self.test_start_time:
#                 elapsed_minutes = (self.frame_count / 30) / 60  # Assuming 30 FPS
#                 if elapsed_minutes > 0:
#                     blink_rate = self.blink_counter / elapsed_minutes
#                     analysis['health_metrics']['blink_rate'] = float(blink_rate)
            
#             # Draw advanced face mesh
#             annotated_frame = frame.copy()
#             annotated_frame = self.draw_advanced_face_mesh(annotated_frame, landmarks, draw_mesh)
#             analysis['frame_annotated'] = annotated_frame
            
#             self.frame_count += 1
        
#         return analysis
    
#     def detect_blink(self, landmarks):
#         """Advanced blink detection with adaptive threshold"""
#         try:
#             left_ear = self.calculate_eye_aspect_ratio(landmarks, self.LEFT_EYE_INDICES)
#             right_ear = self.calculate_eye_aspect_ratio(landmarks, self.RIGHT_EYE_INDICES)
            
#             ear = (left_ear + right_ear) / 2.0
#             self.ear_history.append(ear)
            
#             # Adaptive threshold based on history
#             if len(self.ear_history) > 5:
#                 avg_ear = np.mean(self.ear_history)
#                 adaptive_threshold = avg_ear * 0.7  # 30% drop indicates blink
#             else:
#                 adaptive_threshold = self.BLINK_THRESHOLD
            
#             blink_detected = False
            
#             if ear < adaptive_threshold:
#                 self.eye_closed_frames += 1
#             else:
#                 if self.eye_closed_frames >= self.BLINK_CONSECUTIVE_FRAMES:
#                     self.blink_counter += 1
#                     blink_detected = True
#                     print(f"Blink detected! Total: {self.blink_counter}")
#                 self.eye_closed_frames = 0
            
#             # Calculate blink asymmetry
#             ear_asymmetry = abs(left_ear - right_ear)
            
#             return bool(blink_detected), float(ear), float(ear_asymmetry)
#         except Exception as e:
#             print(f"Blink detection error: {e}")
#         return False, 0.3, 0.0
    
#     def calculate_expression_variability(self):
#         """Calculate how much facial expressions change over time"""
#         if len(self.micro_expression_history) < 2:
#             return 0.0
        
#         variabilities = []
#         for i in range(1, len(self.micro_expression_history)):
#             current = self.micro_expression_history[i]
#             previous = self.micro_expression_history[i-1]
            
#             changes = []
#             for emotion in current:
#                 if emotion in previous:
#                     change = abs(current[emotion] - previous[emotion])
#                     changes.append(change)
            
#             if changes:
#                 variabilities.append(np.mean(changes))
        
#         return float(np.mean(variabilities)) if variabilities else 0.0
    
#     def start_test_session(self):
#         """Start a new test session"""
#         self.blink_counter = 0
#         self.eye_closed_frames = 0
#         self.ear_history.clear()
#         self.micro_expression_history.clear()
#         self.action_unit_history.clear()
#         self.frame_count = 0
#         self.test_start_time = None
    
#     def get_comprehensive_analysis(self, duration_minutes=1.0):
#         """Get comprehensive analysis after test completion"""
#         # Calculate metrics
#         blink_rate = self.blink_counter / duration_minutes if duration_minutes > 0 else 0
        
#         # Get average expressions
#         avg_expressions = self.expression_intensity.copy()
#         if self.micro_expression_history:
#             for emotion in avg_expressions:
#                 values = [expr.get(emotion, 0) for expr in self.micro_expression_history]
#                 avg_expressions[emotion] = int(np.mean(values))
        
#         # Calculate facial asymmetry average
#         facial_asymmetry = 0.0
#         if self.frame_count > 0:
#             # This would need to be tracked during processing
#             pass
        
#         # Create expression pattern for disease prediction
#         expression_patterns = {
#             'reduced_expressivity': avg_expressions['neutral'] > 80,
#             'sad': avg_expressions['sad'],
#             'neutral': avg_expressions['neutral'],
#             'surprised': avg_expressions['surprised'],
#             'weak_eye_closure': False  # This would need specific tracking
#         }
        
#         # Predict health conditions
#         conditions, confidence_scores = self.predict_health_conditions(
#             blink_rate, facial_asymmetry, expression_patterns
#         )
        
#         # Generate recommendations
#         recommendations = self.generate_recommendations(conditions, blink_rate, avg_expressions)
        
#         return {
#             'blink_count': int(self.blink_counter),
#             'blink_rate': float(blink_rate),
#             'avg_expressions': avg_expressions,
#             'facial_asymmetry': float(facial_asymmetry),
#             'conditions': conditions,
#             'confidence_scores': confidence_scores,
#             'recommendations': recommendations,
#             'expression_variability': self.calculate_expression_variability()
#         }
    
#     def generate_recommendations(self, conditions, blink_rate, expressions):
#         """Generate personalized health recommendations"""
#         recommendations = []
        
#         # General recommendations
#         if blink_rate < 8:
#             recommendations.append("Consult an ophthalmologist for dry eye evaluation")
#             recommendations.append("Use artificial tears regularly")
#             recommendations.append("Practice the 20-20-20 rule (every 20 minutes, look at something 20 feet away for 20 seconds)")
        
#         if blink_rate > 25:
#             recommendations.append("Practice stress management techniques")
#             recommendations.append("Ensure 7-8 hours of quality sleep")
#             recommendations.append("Consider mindfulness meditation")
        
#         if expressions.get('sad', 0) > 40:
#             recommendations.append("Consider speaking with a mental health professional")
#             recommendations.append("Engage in regular physical activity")
#             recommendations.append("Maintain social connections")
        
#         # Condition-specific recommendations
#         for condition in conditions:
#             if "Parkinson" in condition:
#                 recommendations.append("Consult a neurologist for comprehensive evaluation")
#                 recommendations.append("Consider physical therapy for facial exercises")
            
#             if "Bell's Palsy" in condition or "Stroke" in condition:
#                 recommendations.append("Seek immediate medical attention if symptoms are new")
#                 recommendations.append("Consult a neurologist for proper diagnosis")
            
#             if "Thyroid" in condition:
#                 recommendations.append("Get thyroid function tests (TSH, T3, T4)")
#                 recommendations.append("Consult an endocrinologist")
            
#             if "Myasthenia Gravis" in condition:
#                 recommendations.append("Consult a neurologist specialized in neuromuscular disorders")
#                 recommendations.append("Consider acetylcholine receptor antibody test")
        
#         # Add general health recommendations
#         if not recommendations:
#             recommendations.append("Continue regular health check-ups")
#             recommendations.append("Maintain a balanced diet and exercise routine")
#             recommendations.append("Monitor any changes in facial movements or blinking patterns")
        
#         return recommendations
import cv2
import mediapipe as mp
import numpy as np
import random
from collections import Counter

mp_face_mesh = mp.solutions.face_mesh

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

def euclidean(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

class EnhancedFaceAnalyzer:
    def __init__(self):
        self.face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)
        self.blink_count = 0
        self.consec_frames = 0
        self.expression_history = []

        self.blink_threshold = 0.21
        self.blink_frames = 3

    def start_test_session(self):
        self.blink_count = 0
        self.consec_frames = 0
        self.expression_history = []

    def calculate_EAR(self, landmarks, eye, w, h):
        points = []
        for idx in eye:
            x = int(landmarks[idx].x * w)
            y = int(landmarks[idx].y * h)
            points.append((x, y))

        A = euclidean(points[1], points[5])
        B = euclidean(points[2], points[4])
        C = euclidean(points[0], points[3])

        ear = (A + B) / (2.0 * C)
        return ear

    def detect_expression(self, landmarks, w, h):
        def to_point(lm):
            return np.array([lm.x * w, lm.y * h])

        # Mouth
        lm = to_point(landmarks[61])
        rm = to_point(landmarks[291])
        ul = to_point(landmarks[13])
        ll = to_point(landmarks[14])

        # Brows and eyes
        lb = to_point(landmarks[70])
        rb = to_point(landmarks[300])
        le = to_point(landmarks[33])
        re = to_point(landmarks[263])

        mouth_width = np.linalg.norm(lm - rm)
        mouth_open = np.linalg.norm(ul - ll)
        brow_height = (np.linalg.norm(lb - le) + np.linalg.norm(rb - re)) / 2

        # Normalize features
        face_scale = np.linalg.norm(le - re) + 1e-6
        mouth_ratio = mouth_width / face_scale
        open_ratio = mouth_open / face_scale
        brow_ratio = brow_height / face_scale

        # Expression scoring
        happy = max(0, (mouth_ratio - 0.45) * 250)
        surprise = max(0, (open_ratio - 0.08) * 400)
        angry = max(0, (0.28 - brow_ratio) * 350)
        sad = max(0, (0.42 - mouth_ratio) * 250)

        # Clamp values
        happy = min(100, happy)
        surprise = min(100, surprise)
        angry = min(100, angry)
        sad = min(100, sad)

        neutral = max(0, 100 - max(happy, surprise, angry, sad))

        scores = {
            "happy": happy,
            "surprise": surprise,
            "angry": angry,
            "sad": sad,
            "neutral": neutral
        }

        # Pick dominant expression
        return max(scores, key=scores.get)

    def process_frame(self, frame, draw_mesh=True):
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        ear = 0
        blink_detected = False
        expressions = {
            "angry": 0,
            "sad": 0,
            "neutral": 0,
            "happy": 0,
            "surprise": 0
        }

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark

            leftEAR = self.calculate_EAR(landmarks, LEFT_EYE, w, h)
            rightEAR = self.calculate_EAR(landmarks, RIGHT_EYE, w, h)
            ear = (leftEAR + rightEAR) / 2.0

            if ear < self.blink_threshold:
                self.consec_frames += 1
            else:
                if self.consec_frames >= self.blink_frames:
                    self.blink_count += 1
                    blink_detected = True
                self.consec_frames = 0

            emotion = self.detect_expression(landmarks, w, h)
            self.expression_history.append(emotion)

            counts = Counter(self.expression_history[-10:])
            total = sum(counts.values())

            for e in expressions:
                if total > 0:
                    expressions[e] = int((counts[e] / total) * 100)

            if draw_mesh:
                mp_drawing = mp.solutions.drawing_utils
                mp_styles = mp.solutions.drawing_styles

                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=results.multi_face_landmarks[0],
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_styles.get_default_face_mesh_tesselation_style()
                )

        return {
            "blink_detected": blink_detected,
            "blink_count": self.blink_count,
            "ear": ear,
            "ear_asymmetry": 0.0,
            "has_face": bool(results.multi_face_landmarks),
            "facial_asymmetry": 0.0,
            "expressions": expressions,
            "action_units": {},
            "health_metrics": {
                "blink_rate": self.blink_count
            },
            "frame_annotated": frame
        }
        
    def predict_neuro_conditions(self, blink_rate, facial_asymmetry, expressions, variability):
        conditions = []
        confidence = {}

        if blink_rate < 8 and variability < 15:
            conditions.append("Parkinson’s Disease")
            confidence["Parkinson’s Disease"] = 75

        if expressions['neutral'] > 80 and variability < 10:
            conditions.append("Autism Spectrum Disorder")
            confidence["Autism Spectrum Disorder"] = 60

        if facial_asymmetry > 0.05:
            conditions.append("Bell’s Palsy")
            confidence["Bell’s Palsy"] = 70

        if facial_asymmetry > 0.1:
            conditions.append("Stroke")
            confidence["Stroke"] = 85

        if expressions['neutral'] > 85 and variability < 12:
            conditions.append("Alzheimer’s Disease")
            confidence["Alzheimer’s Disease"] = 65

        if blink_rate < 12 and variability < 20:
            conditions.append("ALS")
            confidence["ALS"] = 60

        if blink_rate > 30 and variability > 40:
            conditions.append("Tourette Syndrome")
            confidence["Tourette Syndrome"] = 70

        if variability > 60 and blink_rate > 20:
            conditions.append("Huntington’s Disease")
            confidence["Huntington’s Disease"] = 65

        return conditions, confidence

    def calculate_variability(self):
        if len(self.expression_history) < 2:
            return 0

        changes = 0
        for i in range(1, len(self.expression_history)):
            if self.expression_history[i] != self.expression_history[i-1]:
                changes += 1

        variability = (changes / len(self.expression_history)) * 100
        return variability

    def get_comprehensive_analysis(self, duration_minutes):
        if not self.expression_history:
            avg_expressions = {
                "angry": 0,
                "sad": 0,
                "neutral": 100,
                "happy": 0,
                "surprise": 0
            }
        else:
            counts = Counter(self.expression_history)
            total = sum(counts.values())
            avg_expressions = {
                e: int((counts[e] / total) * 100)
                for e in ["angry", "sad", "neutral", "happy", "surprise"]
            }

        blink_rate = 0
        if duration_minutes > 0:
            blink_rate = self.blink_count / duration_minutes

        variability = self.calculate_variability()

        conditions, confidence = self.predict_neuro_conditions(
            blink_rate,
            0.0,
            avg_expressions,
            variability
        )

        recommendations = [
            "Maintain regular sleep schedule",
            "Reduce screen time",
            "Consult a specialist if symptoms persist"
        ]

        return {
            "blink_count": self.blink_count,
            "blink_rate": blink_rate,
            "avg_expressions": avg_expressions,
            "conditions": conditions,
            "confidence_scores": confidence,
            "recommendations": recommendations,
            "facial_asymmetry": 0.0,
            "expression_variability": variability
        }

