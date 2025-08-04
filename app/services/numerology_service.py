# app/services/numerology_service.py

import json
with open("app/data/numerology_meanings.json") as f:
    meanings = json.load(f)

def reduce_number(n):
    if n in [11, 22, 33]: return n
    while n > 9: n = sum(int(d) for d in str(n))
    return n

def life_path(dob):
    digits = [int(c) for c in dob if c.isdigit()]
    return reduce_number(sum(digits))

def expression(name):
    values = {c: (ord(c) - 64) % 9 or 9 for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
    return reduce_number(sum(values.get(c, 0) for c in name.upper() if c.isalpha()))

def soul_urge(name):
    vowels = "AEIOU"
    values = {c: (ord(c) - 64) % 9 or 9 for c in vowels}
    return reduce_number(sum(values.get(c, 0) for c in name.upper() if c in vowels))

def interpret(n): return meanings.get(str(n), "No meaning found.")
