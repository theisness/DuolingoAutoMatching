import pyautogui
import time
import cv2
import numpy as np
from PIL import Image
import pytesseract
from testtrans import AsyncTranslator
import asyncio
from fuzzywuzzy import fuzz

# Configuration
pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

# install url: https://tesseract-ocr.github.io/tessdoc/Installation.html
# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
screenshot_region = (2740, 250, 328, 432)
def take_screenshot():
    """Take a screenshot and return it as a PIL Image"""
    screenshot = pyautogui.screenshot(region=screenshot_region)
    return screenshot

def find_text_locations(image):
    """Find locations of text boxes in the image and separate them into left and right sides"""
    opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
    
    # Threshold the image
    _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    cv2.imshow('binary', binary)
    cv2.waitKey(1)
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter and separate boxes into left and right sides
    left_boxes = []
    right_boxes = []
    image_width = opencv_image.shape[1]
    midpoint = image_width // 2
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 50 and h > 20:  # Filter small boxes
            if (x+w/2) < midpoint:
                left_boxes.append((x, y, w, h))
            else:
                right_boxes.append((x, y, w, h))
            cv2.rectangle(opencv_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    
    # cv2.imshow('Contours', opencv_image)
    # cv2.waitKey(1)

    return left_boxes, right_boxes, opencv_image

def is_chinese(text):
    """Check if text contains Chinese characters"""
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def calculate_similarity(word1, word2):
    """
    计算两个单词的相似度（基于字符串匹配）
    """
    return fuzz.ratio(word1.lower(), word2.lower())


async def click_matching_pairs():
    """Main function to find and click matching word pairs"""
    async with AsyncTranslator() as translator:
        while True:
            print("Looking for word pairs...")
            
            
            # Take screenshot
            screenshot = take_screenshot()
            
            # Find text boxes, separated by side
            left_boxes, right_boxes, opencv_image = find_text_locations(screenshot)
            cv2.imshow('Contours0', opencv_image)
            cv2.waitKey(1)

            # Change tuples to lists for chinese_words and english_words
            chinese_words = []
            english_words = []
            
            # Process left side (Chinese)
            for box in left_boxes:
                x, y, w, h = box
                region = screenshot.crop((x, y, x + w, y + h))
                
                text = pytesseract.image_to_string(region, lang='chi_sim').strip()
                if text:
                    # remove space
                    text=text.replace('\n', '')
                    text = text.replace(' ', '')
                    chinese_words.append([text, box, False])  # Using list instead of tuple
            
            # Process right side (English)
            for box in right_boxes:
                x, y, w, h = box
                region = screenshot.crop((x, y, x + w, y + h))
                text = pytesseract.image_to_string(region, lang='eng').strip()
                if text:
                    english_words.append([text, box, False])  # Using list instead of tuple
            print('get chinese_words: ', chinese_words, 'english_words: ', english_words)

            # Colors table
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), 
                     (255, 0, 255), (0, 255, 255), (255, 255, 255)]
            min_similarity = 80
            # Try to find matching pairs
            for i in range(len(chinese_words)):
                chinese_text, chinese_box, matched = chinese_words[i]
                if matched:
                    continue
                translated = await translator.translate_text(chinese_text)
                if translated:
                    print(f"{chinese_text} -> {translated}")
                    
                    for j in range(len(english_words)):
                        english_text, english_box, matched = english_words[j]
                        if matched:
                            continue
                        similarity = calculate_similarity(translated, english_text)
                        print('similarity: ', similarity)
                        
                        if similarity > min_similarity:
                            print('click')
                            chinese_words[i][2] = True  # Now works because it's a list
                            english_words[j][2] = True  # Now works because it's a list
                            x,y,w,h = chinese_box
                            x2, y2, w2, h2 = english_box
                            pyautogui.click(screenshot_region[0]+x+w/2, screenshot_region[1]+y+h/2)
                            pyautogui.click(screenshot_region[0]+x2+w2/2, screenshot_region[1]+y2+h2/2)
                            cv2.circle(opencv_image, (int(x+w/2), int(y+h/2)), 5, colors[i], -1)
                            cv2.circle(opencv_image, (int(x2+w2/2), int(y2+h2/2)), 5, colors[i], -1)
                    
           
            for i in range(len(english_words)):
                english_text, english_box, matched = english_words[i]
                if matched:
                    continue
                translated = await translator.translate_text(english_text,'en', 'zh-cn')
                if translated:
                    print(f"{english_text} -> {translated}")
                    
                    # ... rest of matching logic ...
                    
                    for j in range(len(chinese_words)):
                        chinese_text, chinese_box, matched = chinese_words[j]
                        if matched:
                            continue
                        similarity = calculate_similarity(translated, chinese_text)
                        print('similarity: ', similarity)
                        
                        if similarity > min_similarity:
                            print('click')
                            english_words[i][2] = True
                            chinese_words[j][2] = True
                            x,y,w,h = chinese_box
                            x2, y2, w2, h2 = english_box
                            pyautogui.click(screenshot_region[0]+x+w/2, screenshot_region[1]+y+h/2)
                            pyautogui.click(screenshot_region[0]+x2+w2/2, screenshot_region[1]+y2+h2/2)
                            cv2.circle(opencv_image, (int(x+w/2), int(y+h/2)), 5, colors[i], -1)
                            cv2.circle(opencv_image, (int(x2+w2/2), int(y2+h2/2)), 5, colors[i], -1)
                    
            cv2.imshow('Contours', opencv_image)
            cv2.waitKey(1)


def main():
    print("Word matching bot starting in 3 seconds...")
    print("Move mouse to corner to abort.")
    
    try:
        asyncio.run(click_matching_pairs())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        # print error code lines
        print(f"An error occurred: {str(e)}")
        print(f"Error traceback: {e.__traceback__}")

if __name__ == "__main__":
    main()
