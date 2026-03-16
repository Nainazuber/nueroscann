/**
 * Enhanced Face Detection with Health Analysis
 */

class EnhancedFaceDetection {
    constructor() {
        // DOM Elements
        this.video = document.getElementById('video-feed');
        this.canvas = document.getElementById('overlay-canvas');
        this.ctx = this.canvas.getContext('2d');
        
        // Stats Elements
        this.blinkCountElement = document.getElementById('blink-count');
        this.blinkRateElement = document.getElementById('blink-rate');
        this.earValueElement = document.getElementById('ear-value');
        
        // Expression Elements
        this.neutralBar = document.getElementById('neutral-bar');
        this.neutralValue = document.getElementById('neutral-value');
        this.happyBar = document.getElementById('happy-bar');
        this.happyValue = document.getElementById('happy-value');
        this.sadBar = document.getElementById('sad-bar');
        this.sadValue = document.getElementById('sad-value');
        this.angryBar = document.getElementById('angry-bar');
        this.angryValue = document.getElementById('angry-value');
        this.surpriseBar = document.getElementById('surprise-bar');
        this.surpriseValue = document.getElementById('surprise-value');

        
        // Progress Elements
        this.timerElement = document.getElementById('timer');
        this.countdownElement = document.getElementById('countdown');
        this.progressBar = document.getElementById('progress-bar');
        this.progressPercent = document.getElementById('progress-percent');
        
        // Control Elements
        this.liveDiagnostics = document.getElementById('live-diagnostics');
        this.healthIndicators = document.getElementById('health-indicators');
        this.completeButton = document.getElementById('complete-btn');
        
        // State Management
        this.stream = null;
        this.isTesting = false;
        this.isCountdown = false;
        this.testStartTime = null;
        this.testDuration = 60;
        this.countdownDuration = 5;
        this.sessionId = document.getElementById('session-id').value;
        
        // Analysis Data
        this.blinkCount = 0;
        this.frameCount = 0;
        this.expressionHistory = [];
        this.healthMetrics = {
            blinkRate: 0,
            facialSymmetry: 1.0,
            expressionVariability: 0
        };
        
        // Settings
        this.drawMesh = true;
        this.showDiagnostics = true;
        
        // Initialize
        this.initializeCamera();
        this.setupEventListeners();
    }
    
    async initializeCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 800 },
                    height: { ideal: 600 },
                    facingMode: 'user',
                    frameRate: { ideal: 30 }
                },
                audio: false
            });
            
            this.video.srcObject = this.stream;
            
            await new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    this.video.play();
                    this.canvas.width = this.video.videoWidth;
                    this.canvas.height = this.video.videoHeight;
                    this.updateCanvas();
                    resolve();
                };
            });
            
            console.log('Camera initialized');
            
        } catch (error) {
            console.error('Camera error:', error);
            this.showCameraError(error);
        }
    }
    
    showCameraError(error) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.innerHTML = `
            <i class="fas fa-video-slash"></i>
            <strong>Camera Error</strong>
            <p>${error.message}</p>
            <button onclick="location.reload()" class="btn btn-sm btn-primary mt-2">
                <i class="fas fa-redo"></i> Retry
            </button>
        `;
        
        document.querySelector('.video-container').innerHTML = '';
        document.querySelector('.video-container').appendChild(errorDiv);
    }
    
    setupEventListeners() {
        // Mesh toggle
        document.getElementById('show-mesh').addEventListener('change', (e) => {
            this.drawMesh = e.target.checked;
        });
        
        // Diagnostics toggle
        document.getElementById('show-diagnostics').addEventListener('change', (e) => {
            this.showDiagnostics = e.target.checked;
            this.liveDiagnostics.style.display = this.showDiagnostics ? 'block' : 'none';
        });
        
        // Visibility change
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isTesting) {
                this.pauseTest();
            }
        });
    }
    
    updateCanvas() {
        if (!this.video.videoWidth) {
            requestAnimationFrame(() => this.updateCanvas());
            return;
        }

        // Only draw raw video when NOT testing
        if (!this.isTesting) {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

            this.ctx.save();
            this.ctx.scale(-1, 1);
            this.ctx.drawImage(
                this.video,
                -this.canvas.width,
                0,
                this.canvas.width,
                this.canvas.height
            );
            this.ctx.restore();
        }

        requestAnimationFrame(() => this.updateCanvas());
    }

    
    // drawGuide() {
    //     const centerX = this.canvas.width / 2;
    //     const centerY = this.canvas.height / 2;
    //     const radius = Math.min(centerX, centerY) * 0.35;
        
    //     // Guide circle
    //     this.ctx.strokeStyle = this.isTesting ? '#10b981' : '#3b82f6';
    //     this.ctx.lineWidth = 3;
    //     this.ctx.setLineDash([8, 8]);
    //     this.ctx.beginPath();
    //     this.ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    //     this.ctx.stroke();
    //     this.ctx.setLineDash([]);
        
    //     // Guide text
    //     this.ctx.fillStyle = this.isTesting ? '#10b981' : '#64748b';
    //     this.ctx.font = 'bold 16px Inter, sans-serif';
    //     this.ctx.textAlign = 'center';
    //     this.ctx.fillText(
    //         this.isTesting ? 'Health Analysis in Progress' : 'Position Face in Center',
    //         centerX,
    //         centerY + radius + 40
    //     );
    // }
    
    startCountdown() {
        if (this.isTesting || this.isCountdown) return;
        
        this.isCountdown = true;
        let countdown = this.countdownDuration;
        
        this.countdownElement.style.display = 'block';
        this.countdownElement.textContent = countdown;
        
        document.querySelectorAll('[onclick*="startTest"]').forEach(btn => {
            btn.disabled = true;
        });
        
        // Show diagnostics
        if (this.showDiagnostics) {
            this.liveDiagnostics.style.display = 'block';
        }
        
        this.updateStatus('countdown', `Starting health analysis in ${countdown}...`);
        
        const countdownInterval = setInterval(() => {
            countdown--;
            this.countdownElement.textContent = countdown;
            
            if (countdown <= 0) {
                clearInterval(countdownInterval);
                this.countdownElement.style.display = 'none';
                this.isCountdown = false;
                this.startTest();
            }
        }, 1000);
    }
    
    startTest() {
        this.isTesting = true;
        this.testStartTime = Date.now();
        this.blinkCount = 0;
        this.frameCount = 0;
        this.expressionHistory = [];
        
        this.updateStatus('testing', 'Comprehensive health analysis in progress...');
        this.updateUI(true);
        
        this.startAnalysisLoop();
        this.startTimer();
        
        console.log('Health analysis started');
    }
    
    startAnalysisLoop() {
        let lastAnalysisTime = Date.now();
        const analysisInterval = 100; // 10 FPS for analysis
        
        const analyze = async () => {
            if (!this.isTesting) return;
            
            const now = Date.now();
            if (now - lastAnalysisTime >= analysisInterval) {
                lastAnalysisTime = now;
                await this.analyzeFrame();
            }
            
            if (this.isTesting) {
                requestAnimationFrame(analyze);
            }
        };
        
        requestAnimationFrame(analyze);
    }
    
    async analyzeFrame() {
        if (!this.isTesting || !this.video.videoWidth) return;
        
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.video.videoWidth;
        tempCanvas.height = this.video.videoHeight;
        const tempCtx = tempCanvas.getContext('2d');
        
        tempCtx.save();
        tempCtx.scale(-1, 1);
        tempCtx.drawImage(this.video, -tempCanvas.width, 0, tempCanvas.width, tempCanvas.height);
        tempCtx.restore();
        
        const imageData = tempCanvas.toDataURL('image/jpeg', 0.8);
        
        try {
            const response = await fetch('/analyze_frame', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: imageData,
                    draw_mesh: this.drawMesh,
                    session_id: this.sessionId,
                    timestamp: Date.now()
                })
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            if (data.error) {
                console.error('Analysis error:', data.error);
                return;
            }
            
            this.frameCount++;
            
            // Update blink data
            if (data.blink_detected) {
                this.blinkCount++;
                this.showBlinkIndicator();
            }
            
            // Update stats
            this.updateStats(data);
            
            // Update expressions
            this.updateExpressions(data.expressions);
            
            // Update health indicators
            this.updateHealthIndicators(data);
            
            // Draw annotated frame
            if (data.annotated_image) {
                this.drawAnnotatedFrame(data.annotated_image);
            }
            
        } catch (error) {
            console.error('Frame analysis error:', error);
        }
    }
    
    drawAnnotatedFrame(imageData) {
        const img = new Image();
        img.onload = () => {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
            this.ctx.save();
            this.ctx.scale(-1, 1);
            this.ctx.drawImage(img, -this.canvas.width, 0, this.canvas.width, this.canvas.height);
            this.ctx.restore();
            
            this.drawGuide();
        };
        img.src = imageData;
    }
    
    showBlinkIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'blink-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: 600;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            z-index: 1000;
            animation: blinkIndicator 1s ease;
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            @keyframes blinkIndicator {
                0% { opacity: 0; transform: translateY(-20px) scale(0.9); }
                20% { opacity: 1; transform: translateY(0) scale(1); }
                80% { opacity: 1; transform: translateY(0) scale(1); }
                100% { opacity: 0; transform: translateY(-20px) scale(0.9); }
            }
        `;
        
        indicator.innerHTML = `
            <i class="fas fa-eye mr-2"></i>
            <span>Blink Detected</span>
            <small style="display: block; opacity: 0.8; font-size: 0.8em; margin-top: 4px;">
                Total: ${this.blinkCount}
            </small>
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            indicator.remove();
            style.remove();
        }, 1000);
    }
    
    updateStats(data) {
        // Blink count
        if (this.blinkCountElement) {
            this.blinkCountElement.textContent = this.blinkCount;
        }
        
        // Blink rate
        if (this.blinkRateElement) {
            const elapsedSeconds = (Date.now() - this.testStartTime) / 1000;
            const blinkRate = elapsedSeconds > 0 ? (this.blinkCount / elapsedSeconds) * 60 : 0;
            this.blinkRateElement.textContent = blinkRate.toFixed(1);
            
            // Color coding
            if (blinkRate < 8) {
                this.blinkRateElement.style.color = '#ef4444';
            } else if (blinkRate > 25) {
                this.blinkRateElement.style.color = '#f59e0b';
            } else {
                this.blinkRateElement.style.color = '#10b981';
            }
        }
        
        // EAR value
        if (this.earValueElement && data.ear) {
            this.earValueElement.textContent = data.ear.toFixed(2);
        }
    }
    
    updateExpressions(expressions) {
        if (!expressions) return;
        
        // Update bars and values
        const updateBar = (bar, value, valueElement) => {
            const percentage = Math.min(100, Math.max(0, value));
            bar.style.width = `${percentage}%`;
            valueElement.textContent = `${Math.round(percentage)}%`;
        };
        
        updateBar(this.neutralBar, expressions.neutral || 0, this.neutralValue);
        updateBar(this.happyBar, expressions.happy || 0, this.happyValue);
        updateBar(this.sadBar, expressions.sad || 0, this.sadValue);
        updateBar(this.angryBar, expressions.angry || 0, this.angryValue);
        updateBar(this.surpriseBar, expressions.surprise || 0, this.surpriseValue);
        
        // Store in history
        this.expressionHistory.push(expressions);
        if (this.expressionHistory.length > 20) {
            this.expressionHistory.shift();
        }
    }
    
    updateHealthIndicators(data) {
        if (!data.health_metrics) return;
        
        const indicators = [];
        
        // Blink rate indicator
        const blinkRate = data.health_metrics.blink_rate || 0;
        if (blinkRate > 0) {
            let blinkStatus = 'normal';
            let blinkIcon = 'fa-check-circle';
            let blinkColor = 'success';
            
            if (blinkRate < 8) {
                blinkStatus = 'low';
                blinkIcon = 'fa-exclamation-triangle';
                blinkColor = 'danger';
            } else if (blinkRate > 25) {
                blinkStatus = 'high';
                blinkIcon = 'fa-exclamation-triangle';
                blinkColor = 'warning';
            }
            
            indicators.push({
                icon: blinkIcon,
                color: blinkColor,
                title: 'Blink Rate',
                value: `${blinkRate.toFixed(1)}/min (${blinkStatus})`
            });
        }
        
        // Facial symmetry indicator
        const symmetry = data.health_metrics.facial_symmetry || 1.0;
        if (symmetry < 0.95) {
            indicators.push({
                icon: 'fa-exclamation-triangle',
                color: 'warning',
                title: 'Facial Asymmetry',
                value: `${((1 - symmetry) * 100).toFixed(1)}% detected`
            });
        }
        
        // Expression variability
        const variability = data.expression_variability || 0;
        if (variability > 0) {
            indicators.push({
                icon: 'fa-smile',
                color: 'success',
                title: 'Expression Range',
                value: `${Math.round(variability)}% variability`
            });
        }
        
        // Update DOM
        this.healthIndicators.innerHTML = indicators.map(ind => `
            <div class="indicator-item ${ind.color}">
                <div class="indicator-icon">
                    <i class="fas ${ind.icon}"></i>
                </div>
                <div class="indicator-content">
                    <div class="indicator-title">${ind.title}</div>
                    <div class="indicator-value">${ind.value}</div>
                </div>
            </div>
        `).join('');
    }
    
    startTimer() {
        const updateTimer = () => {
            if (!this.isTesting) return;
            
            const elapsed = Date.now() - this.testStartTime;
            const remaining = Math.max(0, this.testDuration * 1000 - elapsed);
            const seconds = Math.ceil(remaining / 1000);
            
            // Update timer
            if (this.timerElement) {
                this.timerElement.textContent = `${seconds}s`;
                
                if (seconds <= 10) {
                    this.timerElement.style.color = seconds <= 5 ? '#ef4444' : '#f59e0b';
                    this.timerElement.style.animation = seconds <= 5 ? 'pulse 1s infinite' : 'none';
                }
            }
            
            // Update progress
            if (this.progressBar && this.progressPercent) {
                const progress = ((this.testDuration * 1000 - remaining) / (this.testDuration * 1000)) * 100;
                this.progressBar.style.width = `${progress}%`;
                this.progressPercent.textContent = `${Math.round(progress)}%`;
                
                // Update progress color
                if (progress > 75) {
                    this.progressBar.style.background = '#10b981';
                } else if (progress > 50) {
                    this.progressBar.style.background = '#3b82f6';
                } else if (progress > 25) {
                    this.progressBar.style.background = '#f59e0b';
                }
                
                // Show complete button near end
                if (progress > 90 && this.completeButton) {
                    this.completeButton.style.display = 'inline-block';
                }
            }
            
            // Check completion
            if (remaining <= 0) {
                this.endTest();
            } else {
                setTimeout(updateTimer, 1000);
            }
        };
        
        updateTimer();
    }
    
    async endTest() {
        this.isTesting = false;
        this.completeButton.style.display = 'inline-block';
        this.updateStatus('complete', 'Analysis complete! Click "Complete & Get Report" for results.');
    }
    
    pauseTest() {
        if (!this.isTesting) return;
        
        this.isTesting = false;
        this.updateStatus('paused', 'Analysis paused - window not active');
        
        const resumeDiv = document.createElement('div');
        resumeDiv.className = 'alert alert-warning';
        resumeDiv.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            text-align: center;
        `;
        
        resumeDiv.innerHTML = `
            <i class="fas fa-pause"></i>
            <strong>Analysis Paused</strong>
            <p>Return to window to resume</p>
        `;
        
        document.body.appendChild(resumeDiv);
        
        const resumeHandler = () => {
            if (document.visibilityState === 'visible') {
                this.isTesting = true;
                this.updateStatus('testing', 'Analysis resumed...');
                resumeDiv.remove();
                document.removeEventListener('visibilitychange', resumeHandler);
            }
        };
        
        document.addEventListener('visibilitychange', resumeHandler);
    }
    
    stopTest() {
        if (!this.isTesting && !this.isCountdown) return;
        
        if (confirm('Stop health analysis? All data will be lost.')) {
            this.isTesting = false;
            this.isCountdown = false;
            
            if (this.stream) {
                this.stream.getTracks().forEach(track => track.stop());
            }
            
            this.updateUI(false);
            this.updateStatus('ready', 'Analysis stopped. Ready to start new test.');
            
            if (this.liveDiagnostics) {
                this.liveDiagnostics.style.display = 'none';
            }
            
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        }
    }
    
    updateUI(testing) {
        const controls = document.getElementById('test-controls');
        
        if (testing) {
            if (controls) controls.style.display = 'none';
        } else {
            if (controls) controls.style.display = 'flex';
            
            document.querySelectorAll('[onclick*="startTest"]').forEach(btn => {
                btn.disabled = false;
            });
        }
    }
    
    updateStatus(state, message) {
        const statusElement = document.getElementById('test-status');
        if (!statusElement) return;
        
        statusElement.textContent = message;
        statusElement.className = 'alert';
        
        switch (state) {
            case 'countdown': statusElement.classList.add('alert-warning'); break;
            case 'testing': statusElement.classList.add('alert-info'); break;
            case 'complete': statusElement.classList.add('alert-success'); break;
            case 'paused': statusElement.classList.add('alert-warning'); break;
            default: statusElement.classList.add('alert-secondary');
        }
    }
    
    cleanup() {
        this.isTesting = false;
        this.isCountdown = false;
        
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('video-feed')) {
        window.faceDetection = new EnhancedFaceDetection();
        
        // Global functions
        window.startTest = () => window.faceDetection.startCountdown();
        window.stopTest = () => window.faceDetection.stopTest();
        
        console.log('Enhanced Face Detection initialized');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.faceDetection) {
        window.faceDetection.cleanup();
    }
});