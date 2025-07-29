import os
import numpy as np
import random

from cipherlib.utils import ALPHABET
from cipherlib.bigrams import get_bigrams, transition_matrix_raw


def substitute_encrypt(plaintext, key):
    """
    CZ: Provede substituční šifrování vstupního textu na základě zadaného klíče.
    EN: Encrypts the input text using a substitution cipher based on the provided key.

    Args:
        plaintext (str): CZ: Vstupní text, který má být zašifrován. EN: The input text to be encrypted.
        key (str): CZ: Permutace znaků abecedy. EN: A permutation of the alphabet to use as a substitution key.

    Returns:
        str: CZ: Zašifrovaný text. EN: Encrypted ciphertext.
    """
    mapping = {ALPHABET[i]: key[i] for i in range(len(ALPHABET))}

    # CZ: Kontrola nepovolených znaků / EN: Check for unsupported characters
    invalid_chars = set(plaintext) - set(ALPHABET)
    if invalid_chars:
        raise ValueError(f"Text obsahuje nepovolené znaky / Contains unsupported characters: {invalid_chars}")

    # CZ: Zašifrování znaku dle mapování / EN: Map each character to its encrypted counterpart
    return ''.join(mapping[char] for char in plaintext)


def substitute_decrypt(ciphertext, key):
    """
    CZ: Dešifruje text pomocí inverzní mapy daného klíče.
    EN: Decrypts ciphertext using the inverse of the provided substitution key.

    Args:
        ciphertext (str): CZ: Zašifrovaný text. EN: Encrypted text.
        key (list): CZ: Permutace abecedy použitá při šifrování. EN: The substitution key as a permutation of the alphabet.

    Returns:
        str: CZ: Dešifrovaný text. EN: Decrypted text.
    """
    reverse_mapping = {key[i]: ALPHABET[i] for i in range(len(ALPHABET))}

    # CZ: Kontrola platnosti znaků / EN: Check that all characters are decryptable
    invalid_chars = set(ciphertext) - set(key)
    if invalid_chars:
        raise ValueError(f"Text obsahuje znaky, které nelze dešifrovat / Un-decryptable characters: {invalid_chars}")

    return ''.join(reverse_mapping[char] for char in ciphertext)


def plausibility(text, TM_ref):
    """
    CZ: Vyhodnotí jazykovou pravděpodobnost textu podle referenční bigramové matice.
    EN: Evaluates how linguistically probable a text is based on a reference bigram matrix.

    Args:
        text (str): CZ: Text k vyhodnocení. EN: The decrypted text to evaluate.
        TM_ref (numpy.ndarray): CZ: Normalizovaná bigramová matice. EN: Reference transition matrix (probability-based).

    Returns:
        float: CZ: Logaritmické skóre pravděpodobnosti. EN: Logarithmic likelihood score.
    """
    bigrams_obs = get_bigrams(text)
    TM_obs = transition_matrix_raw(bigrams_obs)
    likelihood = 0

    for i in range(len(ALPHABET)):
        for j in range(len(ALPHABET)):
            if TM_ref[i][j] > 0:
                likelihood += np.log(TM_ref[i][j]) * TM_obs[i][j]

    return likelihood


def prolom_substitute(text, TM_ref, iterations, start_key=None):
    """
    CZ: Používá Metropolis-Hastings algoritmus k prolomení substituční šifry.
    EN: Uses the Metropolis-Hastings algorithm to break a substitution cipher.

    Args:
        text (str): CZ: Šifrovaný text. EN: Encrypted text to analyze.
        TM_ref (numpy.ndarray): CZ: Referenční matice bigramů. EN: Reference bigram transition matrix.
        iterations (int): CZ: Počet iterací algoritmu. EN: Number of iterations to perform.
        start_key (list | None): CZ: Počáteční klíč nebo None pro náhodný. EN: Initial key (or randomly generated if None).

    Returns:
        tuple[str, str, float]: 
            CZ: Nejlepší klíč, dešifrovaný text, a skóre.  
            EN: Best key, corresponding decrypted text, and final plausibility score.
    """
    current_key = list(start_key) if start_key else list(ALPHABET)
    random.shuffle(current_key)

    decrypted_current = substitute_decrypt(text, current_key)
    p_current = plausibility(decrypted_current, TM_ref)

    p_best = p_current
    k_best = current_key

    for i in range(iterations):
        candidate_key = current_key[:]
        idx1, idx2 = random.sample(range(len(ALPHABET)), 2)
        candidate_key[idx1], candidate_key[idx2] = candidate_key[idx2], candidate_key[idx1]

        decrypted_candidate = substitute_decrypt(text, candidate_key)
        p_candidate = plausibility(decrypted_candidate, TM_ref)
        q = p_candidate / p_current if p_current != 0 else 0

        # CZ: Přijímáme horší řešení s malou pravděpodobností / EN: Occasionally accept worse keys to escape local maxima
        if q < 1 or random.uniform(0, 1) < 0.01:
            current_key = candidate_key
            p_current = p_candidate
            if p_best < p_current:
                p_best = p_current
                k_best = current_key

        # CZ: Občasný návrat k nejlepšímu známému řešení / EN: Occasionally reset to best solution found so far
        if i % 1000 == 0:
            print(f"Iteration {i}, current plausibility: {p_current}")
            p_current = p_best
            current_key = k_best

    best_decrypted_text = substitute_decrypt(text, k_best)
    return "".join(k_best), best_decrypted_text, p_best