#=======================
# made by cosmo the deer


#============
import random
import importlib.resources

#=========
info = """
    #-------------------------------------#
    made by cosmo-the-deer 2025 mit license

          
    #------------badcode-help-------------#
    discord: >insert discord server<

          
    #----------------socials--------------#
    discord: cosmothedeer12
    youtube: @cosmo-the-deer
    itch.io: cosmothedeer
    github: cosmo-the-deer
    gmail: [redacted]
          
          
"""

characters_letters = "a b c d e f g h i j k l m n o p q r s t u v w x y z".split()
characters_standard = "a b c d e f g h i j k l m n o p q r s t u v w x y z 1 2 3 4 5 6 7 8 9 0".split()
characters_advanced = "a b c d e f g h i j k l m n o p q r s t u v w x y z 1 2 3 4 5 6 7 8 9 0 ` ~ ! @ # $ % ^ & * ( ) - _ = + [ ] { } \\ | : ; \" \' , < . > / ?".split()
characters_numbers = "1 2 3 4 5 6 7 8 9 0".split()
characters_uwu = "owo uwu :3 >:3)"

def _load_badwords():
    with importlib.resources.open_text('badcode_utilities', 'badwords.txt') as file:
        return [line.strip() for line in file]

bad_words = _load_badwords()


# =========================
def can_str_be_int(string):
    
    """
    check if the passed string "string" can be
    converted to int if true it returns true
    else it returns false
    """

    try:
        int(string)
        return True
    except ValueError:
        return False

# =============================
def str_to_int_or_none(string):
    
    if can_str_be_int(string):
        return int(string)
    else:
        return None

# ====================
def get_yn_bool(text):

    gput = ""
    while gput != "y" and gput != "n":
        gput = input(text).lower()
    return True if gput == "y" else False

# ===================
def get_yn_str(text):

    gput = ""
    while gput.lower() != "y" and gput.lower() != "n":
        gput = input(text)
    return gput
    # i realy want leon from i think i like you

#================
def print_info():
    print(info)

#========
def generate_key(legnth = 10, characters = characters_standard):
    # do you realy think keys are secure.
    key = ""
    for i in range(legnth):
        key = key + random.choice(characters)
    return key

#========
def is_string_bad(string):
    gput = ""
    if any(i in string for i in bad_words):
        return True
    else:
        return False
    
#======================
def filter_string(string = "", replacement_charator = "", words = bad_words):
    filtered = string
    for word in words:
        if word:
            start = 0
            lw = word.lower()
            while True:
                idx = filtered.lower().find(lw, start)
                if idx == -1:
                    break
                filtered = filtered[:idx] + (replacement_charator * len(word)) + filtered[idx+len(word):]
                start = idx + len(word)
    return filtered

def is_string_within(string,range_):
    return len(string) in range_