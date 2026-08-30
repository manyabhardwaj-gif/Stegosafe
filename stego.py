from PIL import Image
import numpy as np

def text_to_bits(text):
    return ''.join(format(byte, '08b') for byte in text.encode('utf-8'))

def hide_message(images_path, secret_message, output_path):
    img = Image.open(images_path)
    arr = np.array(img)
    flat = arr.flatten()

    message_bits = text_to_bits(secret_message)
    length_bits = format(len(message_bits), '032b')   # 32-bit length header
    all_bits = length_bits + message_bits

    if len(all_bits) > len(flat):
        raise ValueError("Message too long for this image.")

    for i, bit in enumerate(all_bits):
        flat[i] = (flat[i] & 0b11111110) | int(bit)

    Image.fromarray(flat.reshape(arr.shape)).save(output_path)

def extract_message(stego_images_path):
    flat = np.array(Image.open(stego_images_path)).flatten()

    length_bits = ''.join(str(flat[i] & 1) for i in range(32))
    msg_len = int(length_bits, 2)

    message_bits = ''.join(str(flat[i] & 1) for i in range(32, 32 + msg_len))
    chars = [message_bits[i:i+8] for i in range(0, len(message_bits), 8)]
    return bytes(int(c, 2) for c in chars).decode('utf-8')

if __name__=="__main__":
    hide_message("images/sample.png","ME AND MY TEAMMATES ARE MANYA,PARAS,MAHI")
# This function reads the hidden bits back out of the image!
def extract_message(image_path):
    img = Image.open(image_path)
    arr = np.array(img)
    flat = arr.flatten()

    # 1. Read the first 32 bits to see how long the secret message is
    length_bits = "".join(str(flat[i] & 1) for i in range(32))
    message_length = int(length_bits, 2)

    # 2. Extract the actual secret message bits based on that length
    message_bits = "".join(
        str(flat[i] & 1) for i in range(32, 32 + message_length)
    )

    # 3. Convert the 0s and 1s back into text characters
    bytes_data = bytearray()
    for i in range(0, len(message_bits), 8):
        byte = message_bits[i : i + 8]
        bytes_data.append(int(byte, 2))

    return bytes(int(c,2)for c in chars).decode("utf-8")
