import random
import string
import cv2
import numpy as np
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QTextEdit, QFileDialog, QVBoxLayout

class SanskritSteganoSystem:
    def __init__(self):
        self.mapping = {
            0: ['अ', 'आ', 'इ', 'ई', 'उ'],
            1: ['ए', 'ऐ', 'ओ', 'औ', 'ऋ'],
            2: ['क', 'ख', 'ग', 'घ', 'ङ'],
            3: ['च', 'छ', 'ज', 'झ', 'ञ'],
            4: ['ट', 'ठ', 'ड', 'ढ', 'ण'],
            5: ['त', 'थ', 'द', 'ध', 'न'],
            6: ['प', 'फ', 'ब', 'भ', 'म'],
            7: ['य', 'र', 'ल', 'व', 'श'],
            8: ['ष', 'स', 'ह', 'ळ', 'क्ष'],
            9: ['ज्ञ', 'त्र', 'श्र', 'ॐ', 'ऽ']
        }
        self.reverse_mapping = {char: num for num, chars in self.mapping.items() for char in chars}
        self.marker = "##SAN##"
    
    def encode_char_to_digits(self, char):
        return [int(digit) for digit in str(ord(char)).zfill(3)]
    
    def decode_digits_to_char(self, digits):
        ascii_val = int(''.join(str(d) for d in digits))
        return chr(ascii_val) if 32 <= ascii_val <= 126 else '?'  # Ensure printable characters
    
    def message_to_numbers(self, message):
        return [digit for char in message for digit in self.encode_char_to_digits(char)]
    
    def numbers_to_message(self, numbers):
        return ''.join(self.decode_digits_to_char(numbers[i:i+3]) for i in range(0, len(numbers), 3))
    
    def numbers_to_sanskrit(self, numbers):
        return self.marker + ' '.join(random.choice(self.mapping[num]) for num in numbers)
    
    def sanskrit_to_numbers(self, text):
        text = text.replace(self.marker, '').strip()
        
        extracted_chars = text.split()
        print(f"Extracted Sanskrit Characters: {extracted_chars}")  # Debugging
        
        numbers = []
        for char in extracted_chars:
            if char in self.reverse_mapping:
                numbers.append(self.reverse_mapping[char])
            else:
                print(f"Unknown Character in Mapping: {char}")  # Debugging

        return numbers

    def encode_message_to_image(self, message, image_path, output_path):
        katapayadi_encoded = self.numbers_to_sanskrit(self.message_to_numbers(message))
        print(f"Encoded Message (Sanskrit): {katapayadi_encoded}")  # Debugging
        
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Image not found or could not be loaded.")
        
        # Convert the Sanskrit message to UTF-8 binary instead of ASCII
        binary_message = ''.join(format(byte, '08b') for byte in katapayadi_encoded.encode('utf-8')) + '1111111111111110'  # End marker
        
        print(f"Binary Encoded Data Length: {len(binary_message)}")  # Debugging

        data_index = 0
        for row in image:
            for pixel in row:
                for i in range(3):
                    if data_index < len(binary_message):
                        pixel[i] = (pixel[i] & ~1) | int(binary_message[data_index])
                        data_index += 1

        cv2.imwrite(output_path, image)

    def decode_message_from_image(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Image not found or could not be loaded.")

        binary_message = ""
        for row in image:
            for pixel in row:
                for i in range(3):
                    binary_message += str(pixel[i] & 1)
                    if binary_message[-16:] == '1111111111111110':
                        binary_message = binary_message[:-16]

                        # Convert binary data back to bytes and decode as UTF-8
                        byte_data = int(binary_message, 2).to_bytes((len(binary_message) + 7) // 8, byteorder='big')
                        try:
                            extracted_text = byte_data.decode('utf-8')  # Decode properly
                        except UnicodeDecodeError:
                            extracted_text = byte_data.decode('latin-1')  # Fallback decoding
                        
                        print(f"Extracted Encoded Sanskrit Text: {extracted_text}")  # Debugging
                        
                        numbers = self.sanskrit_to_numbers(extracted_text)
                        print(f"Extracted Numbers: {numbers}")  # Debugging
                        
                        return self.numbers_to_message(numbers)

        return ""  # Return empty if no message found