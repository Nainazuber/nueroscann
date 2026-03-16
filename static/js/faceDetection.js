class FaceDetection {
    constructor() {
        this.video = document.getElementById('video-feed');
        this.canvas = document.getElementById('overlay-canvas');
        this.ctx = this.canvas.getContext('2d');

        this.blinkCountElement = document.getElementById('blink-count');
        this.blinkRateElement = document.getElementById('blink-rate');
        this.expressionElement = document.getElementById('current-expression');
        this.timerElement = document.getElementById('timer');
        this.progressBar = document.getElementById('progress-bar');
        this.progressPercent = document.getElementById('progress-percent');

        this.stream = null;
        this.isTesting = false;
        this.testStartTime = null;
        this.testDuration = 60;

        this.blinkCount = 0;
        this.frameCount = 0;
        this.expressionData = [];

        this.drawMesh = true;

        this.initializeCamera();
    }

    async initializeCamera() {
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });

            this.video.srcObject = this.stream;

            this.video.onloadedmetadata = () => {
                this.video.play();
                this.canvas.width = this.video.videoWidth;
                this.canvas.height = this.video.videoHeight;
                this.updateCanvas();
            };
        } catch (err) {
            console.error("Camera error:", err);
        }
    }

    updateCanvas() {
        if (!this.video.videoWidth) {
            requestAnimationFrame(() => this.updateCanvas());
            return;
        }

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

        requestAnimationFrame(() => this.updateCanvas());
    }

    startTest() {
        if (this.isTesting) return;

        this.isTesting = true;
        this.testStartTime = Date.now();
        this.blinkCount = 0;
        this.expressionData = [];

        this.analyzeLoop();
        this.startTimer();
    }

    async analyzeLoop() {
        if (!this.isTesting) return;

        await this.analyzeFrame();
        setTimeout(() => this.analyzeLoop(), 200);
    }

    async analyzeFrame() {
        if (!this.video.videoWidth) return;

        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.video.videoWidth;
        tempCanvas.height = this.video.videoHeight;
        const tempCtx = tempCanvas.getContext('2d');

        tempCtx.save();
        tempCtx.scale(-1, 1);
        tempCtx.drawImage(this.video, -tempCanvas.width, 0);
        tempCtx.restore();

        const imageData = tempCanvas.toDataURL('image/jpeg');

        try {
            const res = await fetch('/analyze_frame', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    image: imageData,
                    draw_mesh: true
                })
            });

            const data = await res.json();

            if (data.blink_detected) {
                this.blinkCount++;
            }

            if (data.expressions) {
                this.expressionData.push(data.expressions);
            }

            this.updateStats();

            if (data.annotated_image) {
                this.drawAnnotatedFrame(data.annotated_image);
            }

        } catch (err) {
            console.error("Frame analysis error:", err);
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
        };
        img.src = imageData;
    }

    updateStats() {
        this.blinkCountElement.textContent = this.blinkCount;

        const elapsed = (Date.now() - this.testStartTime) / 1000;
        const rate = elapsed > 0 ? (this.blinkCount / elapsed) * 60 : 0;
        this.blinkRateElement.textContent = rate.toFixed(1);

        if (this.expressionData.length > 0) {
            const last = this.expressionData[this.expressionData.length - 1];
            const dominant = Object.keys(last).reduce((a, b) => last[a] > last[b] ? a : b);
            this.expressionElement.textContent = dominant;
        }
    }

    startTimer() {
        const update = () => {
            if (!this.isTesting) return;

            const elapsed = (Date.now() - this.testStartTime) / 1000;
            const remaining = Math.max(0, this.testDuration - elapsed);

            this.timerElement.textContent = Math.ceil(remaining) + "s";

            const progress = (elapsed / this.testDuration) * 100;
            this.progressBar.style.width = progress + "%";
            this.progressPercent.textContent = Math.round(progress) + "%";

            if (remaining <= 0) {
                this.endTest();
            } else {
                setTimeout(update, 1000);
            }
        };

        update();
    }

    // async endTest() {
    //     this.isTesting = false;

    //     const blinkRate = (this.blinkCount / this.testDuration) * 60;

    //     const res = await fetch('/save_results', {
    //         method: 'POST',
    //         headers: {'Content-Type': 'application/json'},
    //         body: JSON.stringify({
    //             blink_count: this.blinkCount,
    //             blink_rate: blinkRate,
    //             micro_expressions: {}
    //         })
    //     });

    //     const data = await res.json();
    //     if (data.success) {
    //         window.location.href = "/results/" + data.result_id;
    //     }
    // }
    async endTest() {
        this.isTesting = false;
        
        // Show loading state
        this.updateStatus('processing', 'Processing your results...');
        
        try {
            const response = await fetch('/complete_test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    test_duration: this.testDuration
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Show success message with single condition
                const resultDiv = document.createElement('div');
                resultDiv.className = 'alert alert-success';
                resultDiv.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    z-index: 2000;
                    padding: 30px;
                    border-radius: 15px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                    text-align: center;
                    min-width: 400px;
                `;
                
                let conditionHtml = '';
                if (data.primary_condition !== 'No specific condition detected') {
                    conditionHtml = `
                        <div class="mt-3 p-3 ${data.condition_confidence > 70 ? 'bg-danger' : 'bg-warning'} text-white rounded">
                            <h4>${data.primary_condition}</h4>
                            <p>Confidence: ${data.condition_confidence}%</p>
                        </div>
                    `;
                } else {
                    conditionHtml = `
                        <div class="mt-3 p-3 bg-success text-white rounded">
                            <h4>No Specific Condition Detected</h4>
                            <p>Your blink rate is within normal range</p>
                        </div>
                    `;
                }
                
                resultDiv.innerHTML = `
                    <i class="fas fa-check-circle text-success" style="font-size: 48px;"></i>
                    <h3 class="mt-3">Analysis Complete!</h3>
                    <p>Blink Rate: ${data.blink_rate.toFixed(1)} blinks/min</p>
                    <p>Total Blinks: ${data.blink_count}</p>
                    ${conditionHtml}
                    <div class="mt-4">
                        <a href="/results/${data.result_id}" class="btn btn-primary">
                            <i class="fas fa-chart-line"></i> View Detailed Results
                        </a>
                    </div>
                `;
                
                document.body.appendChild(resultDiv);
                
                // Redirect after 5 seconds
                setTimeout(() => {
                    window.location.href = "/results/" + data.result_id;
                }, 5000);
            } else {
                throw new Error('Failed to save results');
            }
        } catch (error) {
            console.error('Error completing test:', error);
            this.updateStatus('error', 'Error processing results. Please try again.');
        }
    }

    stopTest() {
        this.isTesting = false;
        window.location.href = "/dashboard";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("video-feed")) {
        window.faceDetection = new FaceDetection();
        window.startTest = () => window.faceDetection.startTest();
        window.stopTest = () => window.faceDetection.stopTest();
    }
});
