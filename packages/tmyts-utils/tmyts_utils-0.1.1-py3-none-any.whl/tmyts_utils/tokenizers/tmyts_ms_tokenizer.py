import dropbox
import os

from typing import List

from tokenizers import Tokenizer

'''
The MSHFBPETokenizer class is a wrapper around the Tokenizer class from
the Hugging Face Tokenizers library.
It provides a simple interface to encode and decode text.

Args:
    tokenizer_path (str): The path to a pre-trained tokenizer. It assumes
    the file is at Dropbox

Returns:
    None
'''


class MSHFBPETokenizer():
    def __init__(
            self,
            dropbox_path: str,
            local_path: str
            ):

        '''
        The __init__ method initializes the HFBPETokenizer class.
        It creates a new Tokenizer object with a Byte-Pair Encoding (BPE) model
        and a Whitespace pre-tokenizer. The tokenizer will be loaded from the
        file at Dropbox.
        '''

        # ACCESS_TOKENS is provided via shell's environment variable
        if os.getenv("ACCESS_TOKEN"):
            self.read_from_dropbox(
                local_path=local_path,
                dropbox_path=dropbox_path
            )
        else:
            raise ValueError("environment variable ACCES_TOKEN is not defined")

        self.tokenizer: Tokenizer = Tokenizer.from_file(local_path)

    def encode(self, text) -> List[int]:
        '''
        The encode method encodes a text string into a list of token ids using
        the trained tokenizer.

        Args:
            text (str): The text to be encoded.

        Returns:
            List[int]: A list of token ids representing the encoded text.
        '''

        return self.tokenizer.encode(text).ids

    def decode(self, tokens) -> str:
        '''
        The decode method decodes a list of token ids into a text string using
        the trained tokenizer.

        Args:
            tokens (List[int]): A list of token ids to be decoded.

        Returns:
            str: The decoded text string.
        '''

        return self.tokenizer.decode(tokens, skip_special_tokens=True)

    def read_from_dropbox(
            self,
            local_path: str,
            dropbox_path: str
    ):
        dbx: dropbox.Dropbox = dropbox.Dropbox(os.getenv("ACCESS_TOKEN"))

        try:
            metadata, response = dbx.files_download(dropbox_path)
            with open(local_path, 'wb') as f:
                f.write(response.content)
        except dropbox.exceptions.ApiError as e:
            print(f"API error: {e}")
