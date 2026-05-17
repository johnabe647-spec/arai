from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory
os.makedirs('icons', exist_ok=True)

# Icon sizes needed
sizes = [72, 96, 128, 144, 152, 192, 384, 512]

for size in sizes:
    # Create a new image with blue background
    img = Image.new('RGB', (size, size), color='#1f77b4')
    draw = ImageDraw.Draw(img)
    
    # Draw a magnifying glass (simple)
    center = size // 2
    radius = size // 4
    draw.ellipse([center - radius, center - radius, center + radius, center + radius], 
                 outline='white', width=max(1, size // 30))
    
    # Draw handle
    handle_length = radius // 2
    draw.line([center + radius, center + radius, center + radius + handle_length, center + radius + handle_length],
              fill='white', width=max(1, size // 30))
    
    # Save icon
    img.save(f'icon-{size}.png')
    print(f'Created icon-{size}.png')

print('All icons created!')