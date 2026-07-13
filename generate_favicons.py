import os
from PIL import Image, ImageDraw

def generate_assets():
    static_dir = os.path.join(os.path.dirname(__file__), 'app', 'static')
    os.makedirs(static_dir, exist_ok=True)

    # Define colors
    bg_color = (12, 8, 6)     # #0c0806
    acid_green = (115, 212, 29) # #73d41d

    # Create the base master image (180x180 for apple-touch-icon)
    img_180 = Image.new("RGB", (180, 180), bg_color)
    draw = ImageDraw.Draw(img_180)

    # Draw terminal symbol ">" and block "_" cursor in acid green
    # A crisp, clean minimalist brutalist terminal look
    draw.polygon([(40, 50), (90, 90), (40, 130), (55, 130), (105, 90), (55, 50)], fill=acid_green)
    draw.rectangle([115, 115, 145, 130], fill=acid_green)

    # Save Apple Touch Icon
    img_180.save(os.path.join(static_dir, "apple-touch-icon.png"), "PNG")

    # Save 32x32
    img_32 = img_180.resize((32, 32), Image.Resampling.LANCZOS)
    img_32.save(os.path.join(static_dir, "favicon-32x32.png"), "PNG")

    # Save 16x16
    img_16 = img_180.resize((16, 16), Image.Resampling.LANCZOS)
    img_16.save(os.path.join(static_dir, "favicon-16x16.png"), "PNG")

    # Save .ico containing multiple sizes
    ico_img = Image.new("RGB", (32, 32), bg_color)
    ico_draw = ImageDraw.Draw(ico_img)
    ico_draw.polygon([(7, 8), (17, 16), (7, 24), (10, 24), (20, 16), (10, 8)], fill=acid_green)
    ico_draw.rectangle([22, 21, 26, 24], fill=acid_green)
    ico_img.save(os.path.join(static_dir, "favicon.ico"), format="ICO", sizes=[(16, 16), (32, 32)])

if __name__ == "__main__":
    generate_assets()
    print("Favicon assets generated successfully!")
