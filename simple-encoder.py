import sys

def decode_word(word):
    decoded_word = ''
    for i in range(len(word)):
        char_code = ord(word[i])
        decoded_char = chr(char_code - 1)
        decoded_word += decoded_char
    return decoded_word

def encode_word(word):
    encoded_word = ''
    for i in range(len(word)):
        char_code = ord(word[i])
        encoded_char = chr(char_code + 1)
        encoded_word += encoded_char
    return encoded_word

def encode_file(filename):
    encoded_filename = filename[:-4] + "_encoded.txt"

    with open(filename, 'r') as file:
        lines = file.readlines()
    
    encoded_lines = []
    for line in lines:
        encoded_line = encode_word(line.strip()) + '\n'
        encoded_lines.append(encoded_line)
    
    with open(encoded_filename, 'w') as file:
        file.writelines(encoded_lines)

def decode_file(filename):
    encoded_filename = filename[:-4] + "_encoded.txt"
    decoded_filename = filename[:-4:] + "_decoded.txt"
    
    with open(encoded_filename, 'r') as file:
        lines = file.readlines()
    
    decoded_lines = []
    for line in lines:
        decoded_line = decode_word(line.strip()) + '\n'
        decoded_lines.append(decoded_line)
    
    with open(decoded_filename, 'w') as file:
        file.writelines(decoded_lines)

if __name__ == "__main__":
    filename = sys.argv[1]
    encode_file(filename)
    decode_file(filename)