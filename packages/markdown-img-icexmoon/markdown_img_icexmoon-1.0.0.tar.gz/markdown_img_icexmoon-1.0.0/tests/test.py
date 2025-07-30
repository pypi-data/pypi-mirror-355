import sys
sys.path.insert(-2, "D:\\workspace\\markdown-img2\\src")
print(sys.path)
from markdown_img.main import Main
import os
testFile = '.\\markdown_img\\test_image.md'
if os.path.exists(testFile):
    os.remove(testFile)
main = Main()
main.changeImgService("upyun")
main.changeMainPrams({"compress_engine": "tinyPNG"})
main.main(True)