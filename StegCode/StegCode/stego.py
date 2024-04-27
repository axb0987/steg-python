from PIL import Image
import os
import wave
import hashlib



#HELPER FUNCTIONS
#Function converts text to binary. Useful for converting the hidden message into binary
def text_to_binary(text):
    binary_text = ''
    for char in text:
        binary_text += format(ord(char), '08b') #format ensures 8 bit length
    return binary_text

#Function converts binary to text. Useful for converting the encoded message into text
def binary_to_text(binary):
    list = []
    for byte in binary:
        if(byte == '00000000'): #function breaks if 00000000 is reached. this is due to padding the rest of the periodicity with '0'
            break
        list.append(chr(int(byte, 2)))
    text = ''.join(list)
    return text

#Function converts decimal numbers to binary. Useful for changing decimal values from pixel data to binary for bit manipulation
def decimal_to_binary(byte_list):
    binary_list = []
    for byte in byte_list:
        binary = format(byte, '08b') #ensures 8 bit length
        binary_list.append(binary)
    return binary_list

#Function converts binary to decimal. Useful for preparing bytes back into decimal for image creation
def binary_to_decimal(binary_list):
    decimal_list = []
    for byte in binary_list:
        decimal = int(byte, 2)
        decimal_list.append(decimal)
    return decimal_list


#helper function I found to allow for image creation with the proper format
def flat_to_rgb(pixel_data):
    rgb_tuples = [(pixel_data[i], pixel_data[i + 1], pixel_data[i + 2]) for i in range(0, len(pixel_data), 3)]
    return rgb_tuples

def image_init(image_path):
    png_path = convert_to_png(image_path)
    if png_path:
        print("Image converted to PNG:", png_path)

        pixel_data, width, height = extract_pixel_data(png_path)  # gets data from image
        if pixel_data and width and height:  # if extraction worked
            binary_image_data = decimal_to_binary(pixel_data)  # Convert the pixel data to binary
            binary_string = ''.join(binary_image_data)
            return binary_string, width, height

def video_init(video_path):
    try:
        # Open the video file in binary mode
        with open(video_path, "rb") as file:
            # Read all bytes from the file
            video_data = file.read()
            decimal_data = [int(byte) for byte in video_data]
            binary_image_data = decimal_to_binary(decimal_data)
            binary_string = ''.join(binary_image_data)
    except FileNotFoundError:
        print("Error: Video file not found.")
    except Exception as e:
        print("An error occurred:", e)
    return binary_string

def audio_init(audio_path):
    with wave.open(audio_path, 'rb') as wf:
        # Read the audio data as a stream of bytes
        try:
            # Open the WAV file in read mode
            with wave.open(audio_path, 'rb') as wf:
                # Read the audio data as a stream of bytes
                audio_data = wf.readframes(wf.getnframes())
                params = wf.getparams()
                decimal_data = [int(byte) for byte in audio_data]
                binary_image_data = decimal_to_binary(decimal_data)
                binary_string = ''.join(binary_image_data)
        except FileNotFoundError:
            print(f"Error: The file '{audio_path}' does not exist.")
    return binary_string, params
def bytes_sep(binary_image):
    image_list = []
    for i in range(0, len(binary_image), 8):
        image_list.append(binary_image[i:i + 8])
    return binary_to_decimal(image_list)
#NOTE: Several of these helper functions can be optimized, but I chose to mirror functions and keep verbosity to help readability.
#END HELPER FUNCTIONS
#########################################################
#Function that opens file and extracts the data. Returns the data, width, and height of the image
def extract_pixel_data(image_path):
    try:
        with Image.open(image_path) as img:
            img = img.convert('RGB') #Needed to make sure PNG follows format of RGB for bit manipulation

            pixel_data = list(img.tobytes())
            width, height = img.size #only neccessary for creating the new image

            return pixel_data, width, height
    except Exception as e:
        print("Error:", e)
        return None, None, None

#Function that creates an image from given pixel data. The data is given as a list of bytes and then changed to tuples with a helper function
#Had to keep it to png as PNG is a lossless format. Saving as a JPG cost me hours of work trouble shooting only to realize the data changed due to image compression
#cheeky workaround but it makes it so there isnt data loss when creating the image.
def create_image(pixel_data, width, height, filename):
    try:
        data = flat_to_rgb(pixel_data) #function that turns pixel_data, a list of bytes, to tuples
        img = Image.new('RGB', (width, height))

        img.putdata(data)

        png_path = os.path.splitext(filename)[0] + ".png" #Saving as a PNG ensures no data loss when creating or opening the image again
        img.save(png_path, format="PNG")

        return png_path
    except Exception as e:
        print("Error:", e)
        return None

#This function is needed to change JPG images to PNG to ensure no data loss. READ create_image to see my reasoning
def convert_to_png(image_path):
    try:
        img = Image.open(image_path)

        if img.format != "PNG": #errors ocurred when converting png to png, so this is a sanity check to make sure its not already png
            # Convert the image to PNG format
            png_path = os.path.splitext(image_path)[0] + ".png"
            img.save(png_path, format="PNG")
            return png_path
        else:
            return image_path
    except Exception as e:
        print("Error:", e)
        return None

#END IMAGE TRANSFORMATION
def encode_steganography(binary_string, binary_message, L, S, header):
    if len(binary_message)*L + header + S > len(binary_string):
        print("Error: Message is too long to encode in the image.")
        return None
    #A PNG has 8 bytes of header. We will skip this each time to not mess anything up
    # Convert message to binary

    #These indexes do the following:
    message_index = 0 #Keeps track of length of message. when the message bits are consumed, end of message is reached and sub only '0'
    index = 0 #keeps track of the current index, checks if the current bit needs to be replaced by the message bit
    period_index = header*8 + S + L #The next bit to be replaced. Header is skipped, and the Lth bit after the 64th bit will always be chosen. the 65th (i=64) bit will never be modified, even if L = 1
    binary_image = ''
    for bit in binary_string:
        if index != period_index: #checks if current bit needs to be replaced
            binary_image += bit #checks
        elif index == period_index: #replace bit
            if message_index < len(binary_message):
                binary_image += binary_message[message_index]
                message_index += 1
            else:
                binary_image += '0'
            period_index += L
        index += 1

    return binary_image

#This function is essentially the reverse of the first half of the program
def decode_steganography(filename, L, S, header, type):
    binary_string = ''
    if(header == 8):
        binary_string, width, height = image_init(filename)
    elif(header == 44):
        binary_string, params = audio_init(filename)
    elif(header == 1280):
        binary_string= video_init(filename)
    binary_message = ''
    index = 0 #explained in encoding function
    period_index = header * 8 + S + L
    for bit in binary_string:
        if index == period_index:   #This is just the encoding function but rather than replacing bits, it only reads bits following the same algorithm
            binary_message += bit
            period_index += L
        index += 1
    byte_list = []          #verbose but im also not a big python programmer
    for i in range(0, len(binary_message), 8):
        byte_list.append(binary_message[i:i + 8]) #creates a list of bytes
    return binary_to_text(byte_list) #Converts the list of bytes to chars, and then returns it


#END STEGANOGRAPHY
#helper function I found to compare two lists. I had this here to check that the png created and png opened were exactly the same.
def compare_lists(list1, list2):
    if len(list1) != len(list2):
        return False

    for i in range(len(list1)):
        if list1[i] != list2[i]:
            return False

    return True
def print_menu():
    print("Menu:")
    print("1. Image")
    print("2. Video")
    print("3. Audio")
    print("4. Exit")

def print_menu_image():
    print("1.Encode Message")
    print("2.Decode Message")
    print("3.Back")

def print_menu_crypto():
    print("1.Cryptographic Keys")
    print("2.Files")
    print("3.Back")

def print_menu_cryptokeys():
    print("1.Generate Keys")
    print("2.Read Keys")
    print("3.Back")
def print_message_format():
    print("1. Text")
    print("2. Image")
    print("3. Video")
    print("4. Audio")
    inp = input("Enter which medium the message is (Any other number or choice will default to choice 1. Text): ")
    if int(inp) < 1 or int(inp) > 4:
        inp = '1'
    return inp
def input_vars(medium):

    image_path = input("Enter the name of the " + medium + " (with file extension): ")
    S = int(input("Enter the value of S (integer): "))
    if (S < 0):
        S = 0
    L = int(input("Enter the value of L (periodicity/bit to change in every byte): "))
    if (L < 1):
        L = 1
    return image_path, S, L

def decode_vars(medium):
    enc_image_path = input("Enter the name of the " + medium + " to decode (e.g., image.png, audio.wav, video.mp4, etc.): ")
    eS = int(input("Enter the value of S (integer): "))
    eL = int(input("Enter the value of L (periodicity/bit to change in every byte): "))
    return enc_image_path, eS, eL

def message_format_menu(med_choice):
    binary_message = ''
    type = ''
    if med_choice == '1':
        message = input("Enter the message to encode: ")
        binary_message = text_to_binary(message)
        type = 'T'
    elif med_choice == '2':
        message_path = input("Enter the name of the image (with file extension): ")
        binary_message, width, height = image_init(message_path)
        type = 'I'
    elif med_choice == '3':
        message_path = input("Enter the name of the video (with file extension): ")
        binary_string = video_init(message_path)
        type = 'A'
    elif med_choice == '4':
        message_path = input("Enter the name of the audio (with file extension): ")
        binary_string, params = audio_init(message_path)
        type = 'V'
    return binary_message, type
    return None

def main():
    # Prompt user for input
    choice = 0
    while choice != 4:
        print_menu()
        choice = input("Enter your choice: ")

        if choice == '1':
            while choice != 3:
                print_menu_image()
                choice = input("Enter your choice: ")

                if choice == '1':
                    image_path, S, L = input_vars("image")
                    med_choice = print_message_format()
                    message_string, type = message_format_menu(med_choice)
                    binary_string, width, height = image_init(image_path)
                    binary_image = encode_steganography(binary_string, message_string, L, S, 8) #Perform steganography encoding
                    print("Steganography encoding completed")
                    decimal_image_data = bytes_sep(binary_image)

                    create_image(decimal_image_data, width, height, "enc_"+image_path) #Creates the new image. end of steg process, and now proceed to decoding after

                elif choice == '2':
                    enc_image_path, eS, eL = decode_vars("image")
                    hidden_message = decode_steganography(enc_image_path, eL, eS, 8)
                    print(hidden_message)
                elif choice == '3':
                    print("Returning to main menu...")
                    break
                else:
                    print("Invalid choice. Please enter a valid option.")
        elif choice == '2':
            choice = 0
            while choice != 3:
                print_menu_image()
                choice = input("Enter your choice: ")

                if choice == '1':
                    video_path, S, L = input_vars("video")
                    med_choice = print_message_format()
                    message_string, type = message_format_menu(med_choice)

                    binary_string = video_init(video_path)
                    binary_image = encode_steganography(binary_string, message_string, L, S, 1280)  # Perform steganography encoding. we skip 10KB for header, arbitrary but safe value
                    decimal_image_data = bytes_sep(binary_image)

                    video_image_data = bytes(decimal_image_data)
                    try:
                        with open("enc_"+video_path, "wb") as output_file:
                            output_file.write(video_image_data)

                    except FileNotFoundError:
                        print("Error: Video file not found.")
                    except Exception as e:
                        print("An error occurred:", e)

                elif choice == '2':
                    enc_image_path, eS, eL = decode_vars("video")
                    hidden_message = decode_steganography(enc_image_path, eL, eS, 1280)
                    print(hidden_message)
                elif choice == '3':
                    print("Returning to main menu...")
                    break
                else:
                    print("Invalid choice. Please enter a valid option.")
        elif choice == '3':
            choice = 0
            while choice != 3:
                print_menu_image()
                choice = input("Enter your choice: ")

                if choice == '1':
                    audio_path, S, L = input_vars("audio")
                    med_choice = print_message_format()
                    message_string, type = message_format_menu(med_choice)

                    binary_string, params = audio_init(audio_path)
                    binary_image = encode_steganography(binary_string, message_string, L, S,44)  # Perform steganography encoding
                    decimal_image_data = bytes_sep(binary_image)
                    try:
                        with wave.open("enc_"+audio_path, 'wb') as wf:
                            # Set parameters for the WAV file based on the input file
                            wf.setparams(params)

                            # Convert the decimal data back to bytes and write it to the new WAV file
                            wf.writeframes(bytes(decimal_image_data))
                    except FileNotFoundError:
                            print(f"Error: The file '{audio_path}' does not exist.")
                elif choice == '2':
                    enc_image_path, eS, eL = decode_vars("audio")
                    hidden_message = decode_steganography(enc_image_path, eL, eS, 44)
                    print(hidden_message)
                elif choice == '3':
                    print("Returning to main menu...")
                    break
                else:
                    print("Invalid choice. Please enter a valid option.")

        elif choice == '4':
            print("Exiting the program...")
            exit()
        else:
            print("Invalid choice. Please enter a valid option.")



if __name__ == "__main__":
    main()
#This can encode and decode all jpg/png, mp4 and wav. am going to work on putting images inside other formats