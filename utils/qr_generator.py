import pyqrcode
import base64
from io import BytesIO

WEB_APP_URL = "https://your-web-app.com/game"  # Replace with your actual web app URL

def generate_qr_code(game_id):
    """Generate a QR code for the game session and return it as a base64 string."""
    
    # Create the full URL for the game session
    session_url = f"{WEB_APP_URL}?game_id={game_id}"
    
    # Generate QR code
    qr_code = pyqrcode.create(session_url)
    
    # Save QR code to a buffer
    buffer = BytesIO()
    qr_code.svg(buffer, scale=8)
    
    # Convert to base64
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return qr_base64, session_url  # Return the QR code as base64 and the session URL
