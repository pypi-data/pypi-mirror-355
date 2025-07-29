# 📚 cipherlibUnicorn

A Python library for substitution cipher encryption, decryption, and cryptanalysis using bigram matrices and simulated annealing. Built for Czech language texts using Wikisource data.

---

## ✅ JAK TO FUNGUJE

- **`download.py`** – stahuje data knih z Wikisource. Data nejsou přiložena v Gitu, ale mohou být vygenerována skriptem.
- **`bigrams.py`** – práce s maticemi. Ukládají se nenormalizované, aby byly přehledné v celých číslech. `transition_matrix_raw()` se používá pro TM_obs, u které by umělé nahrazování nul jedničkami zhoršovalo výsledky.
- **`encryption.py`** – šifrování, dešifrování a prolomení šifry pomocí algoritmu Metropolis-Hastings.
- **`decipher_all.py`** – hromadné dešifrování (není součástí knihovny, ale některé funkce se mohou hodit).
- **`utils.py`** – obsahuje konstanty jako `ALPHABET` a cesty ke složkám.

---

## ✅ Implementované a zdokumentované funkce požadované v zadání

- **`get_bigrams(text)`** ✅
- **`transition_matrix(bigrams)`** ✅
- **`substitute_encrypt(plaintext, key)`** ✅
- **`substitute_decrypt(ciphertext, key)`** ✅
- **`prolom_substitute(text, TM_ref, iter, start_key=None)`** ✅
- **`plausibility(text, TM_ref)`** ✅

---

## ⚙️ Parametry

- `alphabet` – obsahuje abecedu písmen jako `list`, např. `['A', 'B', ..., '_']`
- `TM_ref` – referenční pravděpodobnostní matice bigramů vytvořená z normálního (nezašifrovaného) textu
- `iter` – počet iterací algoritmu (doporučeno 10k – 50k)
- `start_key` – volitelný uživatelem definovaný počáteční klíč; pokud není zadán, generuje se náhodně
- `text` – zašifrovaný text, na kterém provádíme analýzu

---

## 🚀 Instalace

```
pip install cipherlibUnicorn
```

---

## 📓 Ukázka použití

Viz soubor `notebook_demo.ipynb`, kde je kompletní příklad:
- načtení matice
- šifrování a dešifrování
- prolomení šifry
- uložení výsledků

---

## 🧠 Poznámka

Projekt vznikl jako součást univerzitního zadání pro analýzu substitučních šifer. Zaměřeno na češtinu, ale lze upravit pro jiné jazyky předefinováním abecedy a referenční matice.
