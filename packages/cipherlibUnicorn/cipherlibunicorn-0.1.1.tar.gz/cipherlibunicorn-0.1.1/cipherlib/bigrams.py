import os
import numpy as np

from cipherlib.utils import ALPHABET, MATRIX_PATH


def get_bigrams(text):
    """
    CZ: Vytvoří seznam bigramů (dvojic po sobě jdoucích znaků) z daného textu.
    EN: Generates a list of bigrams (pairs of adjacent characters) from the input text.

    Args:
        text (str): CZ: Vstupní text. EN: Input string.

    Returns:
        list[str]: CZ: Seznam bigramů. EN: List of character bigrams.
    """
    bigrams_list = []
    n = len(text)

    for i in range(n - 1):
        bigram = text[i:i + 2]
        bigrams_list.append(bigram)

    return bigrams_list


def transition_matrix_raw(bigrams):
    """
    CZ: Vytvoří bigramovou (ne-normalizovanou) přechodovou matici s nulovými četnostmi.
    EN: Builds a raw transition matrix (frequencies) from bigrams with 0s preserved.

    Args:
        bigrams (list[str]): Seznam bigramů.

    Returns:
        numpy.ndarray: Matice n x n s počtem výskytů bigramů.
    """
    n = len(ALPHABET)
    TM = np.zeros((n, n), dtype=int)
    char_to_index = {char: i for i, char in enumerate(ALPHABET)}

    for bigram in bigrams:
        c1, c2 = bigram
        if c1 in char_to_index and c2 in char_to_index:
            i, j = char_to_index[c1], char_to_index[c2]
            TM[i, j] += 1
        else:
            raise ValueError(f"Invalid bigram '{bigram}'")

    return TM


def transition_matrix(bigrams):
    """
    CZ: Vytvoří přechodovou matici, kde nuly jsou nahrazeny jedničkami (pro log výpočet).
    EN: Converts the raw matrix into one suitable for log computations by replacing 0s with 1s.

    Args:
        bigrams (list[str]): Seznam bigramů.

    Returns:
        numpy.ndarray: Matice četností přechodů s nenulovými hodnotami.
    """
    TM = transition_matrix_raw(bigrams)
    TM[TM == 0] = 1
    return TM


def create_matrix_from_folder(folder_path):
    """
    CZ: Vytvoří bigramovou přechodovou matici ze všech textových souborů ve složce.
    EN: Builds a transition matrix from all text files in a given folder.

    Args:
        folder_path (str): Cesta ke složce se soubory.

    Returns:
        numpy.ndarray: Matice přechodů napříč všemi texty.
    """
    all_bigrams = []

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        bigrams = get_bigrams(text)
        all_bigrams.extend(bigrams)

    return transition_matrix(all_bigrams)


def normalize_matrix(matrix):
    """
    CZ: Normalizuje číselnou matici tak, aby její součet byl 1 (pravděpodobnosti).
    EN: Normalizes a numerical matrix so that the sum equals 1 (for probabilities).

    Args:
        matrix (numpy.ndarray): Původní matice.

    Returns:
        numpy.ndarray: Normalizovaná matice pravděpodobností.
    """
    matrix[matrix == 0] = 1
    return matrix / np.sum(matrix)


def save_matrix(matrix, file_path):
    """
    CZ: Uloží bigramovou matici do CSV souboru.
    EN: Saves the matrix to a CSV file as integers.

    Args:
        matrix (numpy.ndarray): Matice k uložení.
        file_path (str): Cílová cesta k souboru.
    """
    np.savetxt(file_path, matrix, delimiter=",", fmt="%d")


def load_matrix(file_path):
    """
    CZ: Načte bigramovou matici z CSV souboru.
    EN: Loads a bigram matrix from a CSV file.

    Args:
        file_path (str): Cesta k souboru.

    Returns:
        numpy.ndarray: Načtená matice.
    """
    return np.loadtxt(file_path, delimiter=",", dtype=int)
