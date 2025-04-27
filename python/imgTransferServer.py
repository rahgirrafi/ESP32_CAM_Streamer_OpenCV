import socket
import cv2
import numpy as np
import torch
from threading import Thread
import time

# Check for GPU availability
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Load MiDaS model (small version for real-time performance)
model_type = "MiDaS_small"
midas = torch.hub.load("intel-isl/MiDaS", model_type)
midas.to(device)
midas.eval()

# Load transformations
transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
if model_type == "DPT_Large" or model_type == "DPT_Hybrid":
    transform = transforms.dpt_transform
else:
    transform = transforms.small_transform

class VideoStreamReceiver:
    def __init__(self, host='0.0.0.0', port=8000):
        #log a msg
        print("Initializing VideoStreamReceiver...")
        self.host = host
        self.port = port
        self.running = False
        self.socket = None
        self.thread = None
        self.current_frame = None
        self.current_depth = None
        self.frame_lock = True
        print("VideoStreamReceiver initialized.")

    def start(self):
        print("Starting VideoStreamReceiver...")
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        print(f"Listening on {self.host}:{self.port}")
        
        self.thread = Thread(target=self._receive_frames)
        self.thread.start()
        print("VideoStreamReceiver started.")

    def stop(self):
        print("Stopping VideoStreamReceiver...")
        self.running = False
        if self.socket:
            self.socket.close()
        if self.thread:
            self.thread.join()
        print("VideoStreamReceiver stopped.")

    def _process_depth(self, frame):
        # Ensure the frame is in the correct format
        print("Processing depth...")
        try:
            print("Frame shape:", frame.shape)
            # Convert BGR to RGB
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Apply transforms
            input_batch = transform(img).to(device)
            
            # Predict depth
            with torch.no_grad():
                prediction = midas(input_batch)
                prediction = torch.nn.functional.interpolate(
                    prediction.unsqueeze(1),
                    size=img.shape[:2],
                    mode="bicubic",
                    align_corners=False,
                ).squeeze()
            
            # Convert to numpy and normalize
            depth_map = prediction.cpu().numpy()
            depth_map = cv2.normalize(depth_map, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            depth_map = cv2.applyColorMap(depth_map, cv2.COLORMAP_MAGMA)
            
            return depth_map
        except Exception as e:
            print(f"Depth processing error: {str(e)}")
            return None

    def _receive_frames(self):
        conn, addr = self.socket.accept()
        print(f"Connected to {addr}")
        
        try:
            while self.running:
                # Read frame length header
                print("Waiting for frame header...")
                header = conn.recv(4)
                if len(header) != 4:
                    break
                    
                frame_len = int.from_bytes(header, byteorder='little')
                
                # Read frame data
                print(f"Receiving frame of length: {frame_len}")
                chunks = []
                bytes_received = 0
                while bytes_received < frame_len:
                    print(f"Receiving chunk: {bytes_received}/{frame_len}")
                    chunk = conn.recv(min(frame_len - bytes_received, 4096))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    bytes_received += len(chunk)
                
                # Process complete frame
                if bytes_received == frame_len:
                    print(f"Received complete frame of length: {bytes_received}")
                    frame_data = b''.join(chunks)
                    image = np.frombuffer(frame_data, dtype=np.uint8)
                    frame = cv2.imdecode(image, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        self.current_frame = frame
                        # Process depth map
                        self.current_depth = self._process_depth(frame)
        finally:
            conn.close()
            print("Connection closed")

    def show_video(self):
        while self.running:
            if self.current_frame is not None and self.current_depth is not None:
                # Resize depth map to match frame size
                depth_resized = cv2.resize(self.current_depth, 
                                         (self.current_frame.shape[1], self.current_frame.shape[0]))
                
                # Combine frames side by side
                combined = np.hstack((self.current_frame, depth_resized))
                
                # Display
                cv2.imshow('ESP32-CAM Stream | Depth Map', combined)
                
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop()
                break
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # First-time setup instructions
    print("Note: This code requires:")
    print("- torch and torchvision installed")
    print("- OpenCV-contrib installed")
    print("- Internet connection for model download")
    
    receiver = VideoStreamReceiver()
    receiver.start()
    
    try:
        receiver.show_video()
    except KeyboardInterrupt:
        receiver.stop()