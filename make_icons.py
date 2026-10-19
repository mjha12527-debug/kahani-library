from PIL import Image, ImageDraw
src = Image.open("logo.png").convert("RGBA")
w, h = src.size
s = min(w, h)
l, t = (w - s) // 2, (h - s) // 2
src = src.crop((l, t, l + s, t + s))
def plain(n, name):
    src.resize((n, n), Image.LANCZOS).save(name)
def padded(n, name, ratio):
    bg = Image.new("RGBA", (n, n), (122, 59, 18, 255))
    k = int(n * ratio)
    logo = src.resize((k, k), Image.LANCZOS)
    mask = Image.new("L", (k, k), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, k - 1, k - 1), fill=255)
    bg.paste(logo, ((n - k) // 2, (n - k) // 2), mask)
    bg.convert("RGB").save(name)
plain(192, "icon-192.png")
plain(512, "icon-512.png")
padded(512, "maskable-512.png", 0.62)
padded(180, "apple-touch-icon.png", 0.86)
print("आइकन बन गए")
