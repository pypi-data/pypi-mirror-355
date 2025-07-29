import os

ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ_")

# Path to downloaded cleaned book text
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "resources", "book")

# Path to saved transition matrix
MATRIX_PATH = os.path.join(os.path.dirname(__file__), "resources", "bigram_matice.csv")
