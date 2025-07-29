import spacy
import re,os,shutil,hashlib,base64

class SemanticTextSplitter:
    """
    A class for splitting text into semantic chunks without breaking sentences, utilizing spaCy's NLP capabilities.
    This class ensures that chunks are split at sentence boundaries whenever possible, providing more meaningful text segments.

    Parameters:
    - chunk_size (int): Maximum length of each text chunk in characters.
    - chunk_overlap (int): Number of characters each chunk can overlap with the next chunk. If less than 1, it is taken as a fraction of the chunk_size. 
       Note: When overlapped is used, it will violate the sentence boundary.
    - skip_chunk (int): Number of initial chunks to skip in the final output.
    - skip_char (int): Number of characters to skip at the beginning of the text, aligning to the nearest sentence boundary.
    - model (str): spaCy model identifier to be used for sentence tokenization and boundary detection.

    Usage:
    ```python
    # Example text
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat."
    
    # Create an instance of SemanticTextSplitter
    splitter = SemanticTextSplitter(chunk_size=100, model="en_core_web_sm")
    
    # Split the text and print the results
    chunks = splitter.split_text(text)
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}: {chunk}")
    ```

    This will split the text into chunks of up to 100 characters, each aligning with sentence boundaries as closely as possible.
    """    
    
    def __init__(self, chunk_size:int=None, chunk_overlap:float = None, skip_chunk:int = None, skip_char:int = None, model:str = None):
        
        if chunk_size is None:
            chunk_size = 1000           # Default chunk size
        if chunk_overlap is None:
            chunk_overlap = 0.1         # Default chunk overlap
        if skip_chunk is None:
            skip_chunk = 0              # Default number of chunks to skip
        if skip_char is None:
            skip_char = 0               # Default number of characters to skip
        if model is None:
            model = "en_core_web_sm"    # Default spaCy model

        self._validate_init(chunk_size, chunk_overlap, skip_chunk, skip_char, model)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.skip_chunk = skip_chunk
        self.skip_char = skip_char
        self.nlp = spacy.load(model)

    def _validate_init(self, chunk_size, chunk_overlap, skip_chunk, skip_char, model):
        if not (isinstance(chunk_size, int) and chunk_size > 0):
            raise ValueError("chunk_size must be a positive integer")
        if not (isinstance(chunk_overlap, (int, float)) and 0 <= chunk_overlap < chunk_size):
            raise ValueError("chunk_overlap must be a non-negative number smaller than chunk_size")
        if not (isinstance(skip_chunk, int) and skip_chunk >= 0):
            raise ValueError("skip_chunk must be a non-negative integer")
        if not (isinstance(skip_char, int) and skip_char >= 0):
            raise ValueError("skip_char must be a non-negative integer")
        if not (isinstance(model, str) and model.strip()):
            raise ValueError("model must be a non-empty string")
        
    def _find_sentence_boundary(self, text, skip_char):
        """
        Adjusts the skip_char to the start of the nearest complete sentence following the skip_char,
        considering a buffer around the skip_char for efficient processing.
        """
        if skip_char == 0:
            return 0  # Start from the beginning if no skip is required
        buffer_size = 1000  # Define a buffer size for contextual processing

        # Determine the range of text to analyze with spaCy
        end_index = min(len(text), skip_char + buffer_size)  # Ensure end index doesn't exceed text length

        doc = self.nlp(text[:end_index])  # Process only the relevant part of the text

        # Find the first sentence starting after skip_char within the buffered range
        boundary = next((sent.end_char for sent in doc.sents if sent.start_char >= skip_char), skip_char)
        return max(0, boundary)  # Adjust boundary relative to the full text
    
    def _recursive_text_splitter(self, text, chunk_size):
        
        
        if len(text) <= chunk_size:
            if not text:
                return []
            else:
                return [text]
            #return [text]

        #buffer_size = int(0.1*chunk_size)  # Buffer to ensure sentence completeness
        buffer_size = 1000
        safe_end = min(chunk_size + buffer_size, len(text))
        doc = self.nlp(text[:safe_end])
        boundary_idx = chunk_size

        found=False
        for sent in doc.sents:
            if sent.end_char >= chunk_size and found:
                # If the sentence boundary is found after the chunk_size, that means the sentence is too long.
                # That is why we cannot break too early.
                break
            boundary_idx = sent.end_char
            found=True

        first_part = text[:boundary_idx].strip()
        if self.chunk_overlap > 0:
            if self.chunk_overlap > 1:
                first_part_size_with_overlap = len(first_part)+self.chunk_overlap
            elif self.chunk_overlap < 1:
                first_part_size_with_overlap = len(first_part) + int((self.chunk_overlap)*chunk_size)
            first_part_size_with_overlap = min(first_part_size_with_overlap, len(text))
            first_part = text[:first_part_size_with_overlap].strip()

        rest = text[boundary_idx:].strip()

        # Handle the remaining text by checking if it's smaller than chunk_size but not empty
        if len(rest) <= chunk_size and rest:
            return [first_part, rest]
        else:
            return [first_part] + self._recursive_text_splitter(rest, chunk_size)    

    def split_text(self, text):
        """ Public method to initiate the text splitting process after skipping initial characters and chunks. """
        start_index = self._find_sentence_boundary(text, self.skip_char)
        text=text[start_index:]
        chunks = self._recursive_text_splitter(text, self.chunk_size)
        return chunks[self.skip_chunk:]    

    '''
    Name: get_chunk_subdir
    Description:
        A helper method to transform a file path or url into a subdirectory name for storing the chunks.
        It replaces the non-alphanumeric characters found as part of a path name with underscores and removes the leading underscores.
        If path_or_url is not provided, a non-hyphenated GUID named subdirectory is created instead.
    Example:
        get_chunk_dir("/tmp","test.txt") will return a directory path "/tmp/test"
        get_chunk_dir("/tmp","https://www.example.com/test.txt") will return a directory path "/tmp/www_example_com_test"
    '''
    @classmethod
    def get_output_subdir(cls,path_or_url):
        def is_url(s):
            return re.match(r'^https?:\/\/.*[\r\n]*', s) is not None
        if (is_url(path_or_url)):
            # Create a directory path based on a URL by replacing all url special characters
            path_or_url = path_or_url.replace("://","_").replace("/","_").replace(".","_")
        else:
            # Create a directory path based only on the name part of a file path, ie. name  without extension
            path_or_url = os.path.basename(path_or_url).replace('.','_')
        return re.sub(r'^_+', '', path_or_url)

    '''
    Name: create_base64_chunk_id
    Description:
        Generates a Base64 encoded SHA-256 hash of the input text.
    Parameters:
        text (str or bytes): The input text to hash.
    Returns:
        str: The Base64 encoded SHA-256 hash of the input text.
    '''
    @classmethod
    def create_base64_chunk_id(cls, text):
        if isinstance(text, bytes):
            byte_text = text
        else:
            # If 'text' is not a byte string (assuming it's a str), encode it
            byte_text = text.encode('utf-8')
        
        # Generate SHA256 hash (in binary form)
        hash_digest = hashlib.sha256(byte_text).digest()
        
        # Convert the binary hash to URL and filesystem safe Base64
        base64_encoded_safe = base64.urlsafe_b64encode(hash_digest).decode().rstrip('=')
        
        return base64_encoded_safe

    '''
    Name: create_hex_chunk_id
    Description:
        The function uses sha256 to create a unique id in hexadecimal for the chunk.
    Parameters:
        text: The input text to be converted in SHA256 hash hexadecimal.
    Example:
        create_hex_chunk_id("This is a test") will return the SHA256 hash of the input text.
    '''
    @classmethod
    def create_hex_chunk_id(cls,text):
        import hashlib
        if isinstance(text, bytes):
            byte_text = text
        else:
            # If 'text' is not a byte string (assuming it's a str), encode it
            byte_text = text.encode('utf-8')    
        return hashlib.sha256(byte_text).hexdigest()


    '''
    Name: split_file
    Description:
        The function utilizes _recursive_text_splitter to split the text into chunks and write each chunk into a subdirectory.
    Parameters:
        text: The input text to be split into chunks.
        output_dir: (default:None) /tmp/chunks/{output_dir} for saving the chunks.
        chunk_size: (default:2000) The size of each chunk in characters.
        chunk_overlap: (default:200) The overlap between chunks in characters.
    Output:
        dest_dir: Directory path is returned as output - /tmp/chunks/{output_dir}
        chunks are saved into files with using their hash as chunk_id in order to save space and avoid being spammed.
    Example:
        split_text("This is a test",chunk_overlap=200,chunk_overlap=0) will create files:
        /tmp
            /chunks
                /<sub_dir>
                    <chunk-01-hash>
                    <chunk-02-hash>
                    <chunk-03-hash>
                    ....
        output: /tmp/chunks/<sub_dir>
    '''
    def split_file(self, file_path, output_subdir=None):

        # Read from source and split the text into chunks

        with open(file_path, "r") as file:
            text = file.read()
        chunks = self.split_text(text)
        
        # Create output directory to save the chunk files
        # If output_dir is not provided, use the base name of the file as the output directory name        
        base_dir='/tmp/chunks'
        if (output_subdir is None):
            output_subdir = self.get_output_subdir(file_path)

        dest_dir = os.path.join(base_dir,output_subdir)
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)    
        os.makedirs(dest_dir)
        
        for chunk in chunks:
            chunk_fname = self.create_base64_chunk_id(chunk)
            chunk_fname = os.path.join(dest_dir,chunk_fname)

            # Start writing the chunk
            with open(chunk_fname,'w') as f:
                f.write(chunk)
        return dest_dir
        
