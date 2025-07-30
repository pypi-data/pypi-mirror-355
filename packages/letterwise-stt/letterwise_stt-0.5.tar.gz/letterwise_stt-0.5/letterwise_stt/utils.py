phoneme_to_letter = {
    'AA': 'a', 'AE': 'a', 'AH': 'a', 'AO': 'o', 'AW': 'aw',
    'AY': 'ay', 'B': 'b', 'CH': 'ch', 'D': 'd', 'DH': 'th',
    'EH': 'e', 'ER': 'er', 'EY': 'ey', 'F': 'f', 'G': 'g',
    'HH': 'h', 'IH': 'i', 'IY': 'ee', 'JH': 'j', 'K': 'k',
    'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ng', 'OW': 'o',
    'OY': 'oy', 'P': 'p', 'R': 'r', 'S': 's', 'SH': 'sh',
    'T': 't', 'TH': 'th', 'UH': 'u', 'UW': 'oo', 'V': 'v',
    'W': 'w', 'Y': 'y', 'Z': 'z', 'ZH': 'zh'
}

def phonemes_to_letters(phoneme_str: str) -> str:
    phonemes = phoneme_str.strip().split()
    letters = []
    for p in phonemes:
        p = ''.join([c for c in p if not c.isdigit()])
        letter = phoneme_to_letter.get(p, '')
        letters.append(letter)
    return ''.join(letters)
