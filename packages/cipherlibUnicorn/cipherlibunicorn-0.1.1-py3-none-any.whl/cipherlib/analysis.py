import os
import re
import time

from bigrams import load_matrix, normalize_matrix
from cipherlib.utils import MATRIX_PATH
from cipherlib.encryption import prolom_substitute

# Soubory pro
TEST_FILES_PATH = os.path.join("resources", "Testovaci_soubory")

#text_250_sample_3_ciphertext.txt

#Každý text který automatizovaně pak dešifrujete (stačí u každého textu udělat 20 tisíc pokusů o dešiforvání – iterací algoritmu)
#pak uložíte – i jeho klíč. Kde struktura souborů je: „text_{délka_textu}_sample_{id textu}_plaintext/key.txt“.
#Tedy pro text o délce 1000 a id 20 pak uložíte následující soubory: dešifrovaný text bude uložen jako „text_1000_sample_20_plaintext.txt“


#Dešifrovaný klíč bude uložen jako „text_1000_sample_20_key.txt“
#Kde bude čistě jen text.


def get_file_names(path):
    """
    Zkontroluje, zda soubory ve složce odpovídají očekávanému formátu názvu a vrátí jejich názvy.

    Args:
        path (str): Cesta ke složce se soubory.

    Returns:
        list[str]: Seznam platných názvů souborů.
    """
    # Regulární výraz odpovídající vzoru "text_<číslo>_sample_<číslo>_ciphertext.txt"
    pattern = re.compile(r"^text_\d+_sample_\d+_ciphertext\.txt$")

    file_names = []

    for nazev_souboru in os.listdir(path):
        if not pattern.match(nazev_souboru):
            print(f"Chybný název souboru pro dešifrování: {nazev_souboru}")
        else:
            file_names.append(os.path.join(path, nazev_souboru))

    return file_names


if __name__ == "__main__":

    TM_ref = normalize_matrix(load_matrix(MATRIX_PATH))
    iterations = 20_000

    file_names = get_file_names(TEST_FILES_PATH)

    start = time.time()
    counter = 0

    for file in file_names:

        print("")
        print("Prolamuji: " + file)
        print("")

        with open(file, "r", encoding="utf-8") as f:
            obsah = f.read()

        k_best, best_decrypted_text, p_best = prolom_substitute(obsah, TM_ref, iterations)

        plaintext_file = file.replace("ciphertext", "plaintext")
        key_file = file.replace("ciphertext", "key")

        with open(plaintext_file, "w", encoding="utf-8") as f:
            f.write(best_decrypted_text)

        with open(key_file, "w", encoding="utf-8") as f:
            f.write(k_best)

        end = time.time()
        elapsed = end - start
        minutes = int(elapsed // 60)
        seconds = elapsed % 60
        print("")
        print(f"Čas běhu skriptu: {minutes} min {seconds:.2f} s")
        counter += 1
        print(f"Zpracováno souborů: {counter}")

    print("")
    print("FINISHED!")
    print("")


