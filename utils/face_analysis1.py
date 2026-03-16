import cv2
import numpy as np
import random
from collections import Counter
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python.vision import FaceMesh


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
        self.blink_timings = []
        self.blink_durations = []
        self.ear_history = []  # Store EAR values for pattern analysis

        self.blink_threshold = 0.21
        self.blink_frames = 3
        self.fps = 30
        self.frame_count = 0
        self.blink_start_frame = 0

    def start_test_session(self):
        self.blink_count = 0
        self.consec_frames = 0
        self.expression_history = []
        self.blink_timings = []
        self.blink_durations = []
        self.ear_history = []
        self.frame_count = 0

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

        lm = to_point(landmarks[61])
        rm = to_point(landmarks[291])
        ul = to_point(landmarks[13])
        ll = to_point(landmarks[14])

        lb = to_point(landmarks[70])
        rb = to_point(landmarks[300])
        le = to_point(landmarks[33])
        re = to_point(landmarks[263])

        mouth_width = np.linalg.norm(lm - rm)
        mouth_open = np.linalg.norm(ul - ll)
        brow_height = (np.linalg.norm(lb - le) + np.linalg.norm(rb - re)) / 2

        face_scale = np.linalg.norm(le - re) + 1e-6
        mouth_ratio = mouth_width / face_scale
        open_ratio = mouth_open / face_scale
        brow_ratio = brow_height / face_scale

        happy = max(0, (mouth_ratio - 0.45) * 250)
        surprise = max(0, (open_ratio - 0.08) * 400)
        angry = max(0, (0.28 - brow_ratio) * 350)
        sad = max(0, (0.42 - mouth_ratio) * 250)

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
            self.ear_history.append(ear)

            if ear < self.blink_threshold:
                if self.consec_frames == 0:
                    self.blink_start_frame = self.frame_count
                self.consec_frames += 1
            else:
                if self.consec_frames >= self.blink_frames:
                    self.blink_count += 1
                    blink_detected = True
                    
                    blink_duration = self.consec_frames / self.fps
                    self.blink_durations.append(blink_duration)
                    self.blink_timings.append(self.frame_count / self.fps)
                    
                self.consec_frames = 0

            self.frame_count += 1

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
    
    def analyze_blink_patterns(self, duration_minutes):
        """Analyze blink patterns independently from expressions"""
        if duration_minutes <= 0 or self.blink_count == 0:
            return {
                "avg_blink_rate": 0,
                "blink_variability": 0,
                "avg_blink_duration": 0,
                "blink_regularity": 0,
                "blink_duration_std": 0
            }
        
        blink_rate = self.blink_count / duration_minutes
        
        avg_blink_duration = np.mean(self.blink_durations) if self.blink_durations else 0
        blink_duration_std = np.std(self.blink_durations) if len(self.blink_durations) > 1 else 0
        
        if len(self.blink_timings) > 1:
            intervals = np.diff(self.blink_timings)
            blink_regularity = 1 - (np.std(intervals) / (np.mean(intervals) + 1e-6))
            blink_regularity = max(0, min(1, blink_regularity))
        else:
            blink_regularity = 0
            
        if len(self.blink_timings) > 5:
            segment_size = max(1, len(self.blink_timings) // 5)
            rates = []
            for i in range(0, len(self.blink_timings), segment_size):
                segment = self.blink_timings[i:i+segment_size]
                if len(segment) > 1:
                    segment_rate = len(segment) / (segment[-1] - segment[0] + 1e-6)
                    rates.append(segment_rate)
            blink_variability = np.std(rates) if rates else 0
        else:
            blink_variability = 0
            
        return {
            "avg_blink_rate": blink_rate,
            "blink_variability": blink_variability,
            "avg_blink_duration": avg_blink_duration,
            "blink_duration_std": blink_duration_std,
            "blink_regularity": blink_regularity
        }
    
    def predict_single_disease_from_blink(self, blink_rate, blink_patterns):
        """
        Predict a SINGLE most likely disease based on blink patterns
        Returns ONE disease with confidence score
        """
        avg_blink_duration = blink_patterns.get("avg_blink_duration", 0)
        blink_regularity = blink_patterns.get("blink_regularity", 0)
        blink_variability = blink_patterns.get("blink_variability", 0)
        
        # Based on YOUR specified blink rate ranges
        if blink_rate < 8:
            # Very low blink rate
            return {
                "primary_condition": "Parkinson's Disease",
                "confidence": 85
            }
        
        elif 8 <= blink_rate <= 11:
            # Low blink rate
            return {
                "primary_condition": "Hyperthyroidism",
                "confidence": 80
            }
        
        elif 12 <= blink_rate <= 18:
            # Normal range
            return {
                "primary_condition": "No specific condition detected",
                "confidence": 95
            }
        
        elif 19 <= blink_rate <= 21:
            # Slightly elevated
            return {
                "primary_condition": "Artison / Dry Eye Syndrome",
                "confidence": 75
            }
        
        elif 22 <= blink_rate <= 25:
            # Elevated
            return {
                "primary_condition": "ALS / Motor Neuron Disease",
                "confidence": 80
            }
        
        elif 26 <= blink_rate <= 30:
            # High blink rate
            return {
                "primary_condition": "Bell's Palsy",
                "confidence": 70
            }
        
        else:  # blink_rate >= 31
            # Very high blink rate
            return {
                "primary_condition": "Tourette Syndrome / Tic Disorder",
                "confidence": 85
            }

    def calculate_variability(self):
        """Calculate expression variability (independent)"""
        if len(self.expression_history) < 2:
            return 0

        changes = 0
        for i in range(1, len(self.expression_history)):
            if self.expression_history[i] != self.expression_history[i-1]:
                changes += 1

        variability = (changes / len(self.expression_history)) * 100
        return variability

    def get_comprehensive_analysis(self, duration_minutes):
        """
        Get comprehensive analysis with:
        - Single disease prediction based ONLY on blink patterns
        - Independent expression analysis
        """
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
        
        # Analyze blink patterns independently
        blink_patterns = self.analyze_blink_patterns(duration_minutes)
        
        # Get SINGLE disease prediction based ONLY on blink data
        disease_result = self.predict_single_disease_from_blink(blink_rate, blink_patterns)

        # General recommendations based on the detected condition
        recommendations = ["Maintain regular sleep schedule", "Reduce screen time"]
        
        if disease_result["primary_condition"] != "No specific condition detected":
            condition = disease_result["primary_condition"]
            
            if "Parkinson" in condition:
                recommendations = [
                    "Consult a neurologist for Parkinson's evaluation",
                    "Consider physical therapy for facial exercises",
                    "Regular eye check-ups recommended",
                    "Medication management may be needed"
                ]
            elif "Hyperthyroidism" in condition:
                recommendations = [
                    "Get thyroid function tests (TSH, T3, T4)",
                    "Consult an endocrinologist",
                    "Monitor for symptoms like weight loss, rapid heartbeat",
                    "Avoid caffeine and stimulants"
                ]
            elif "Artison" in condition or "Dry Eye" in condition:
                recommendations = [
                    "Use artificial tears regularly",
                    "Practice the 20-20-20 rule (every 20 minutes, look 20 feet away for 20 seconds)",
                    "Consult an ophthalmologist",
                    "Consider omega-3 supplements for eye health"
                ]
            elif "ALS" in condition:
                recommendations = [
                    "Seek immediate neurological consultation",
                    "Regular monitoring of symptoms",
                    "Consider respiratory function assessment",
                    "Join support groups for ALS patients"
                ]
            elif "Bell's Palsy" in condition:
                recommendations = [
                    "Consult a neurologist immediately",
                    "Protect the affected eye with eye drops and patch at night",
                    "Consider physical therapy for facial muscles",
                    "Most cases recover within 3-6 months"
                ]
            elif "Tourette" in condition:
                recommendations = [
                    "Consult a neurologist for tic evaluation",
                    "Consider behavioral therapy (CBT)",
                    "Monitor tic patterns and triggers",
                    "Medication may help manage symptoms"
                ]

        return {
            # Blink-related outputs
            "blink_count": self.blink_count,
            "blink_rate": blink_rate,
            "blink_patterns": blink_patterns,
            
            # SINGLE disease prediction (most accurate)
            "primary_condition": disease_result["primary_condition"],
            "condition_confidence": disease_result["confidence"],
            
            # Expression-related outputs (independent)
            "avg_expressions": avg_expressions,
            "expression_variability": variability,
            
            # Recommendations based on the detected condition
            "recommendations": recommendations,
            "facial_asymmetry": 0.0,
        }
