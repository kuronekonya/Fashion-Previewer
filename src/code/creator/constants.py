
# ---------------------------------------------------------
# CONSTANTS & METADATA
# ---------------------------------------------------------
CHARACTERS = ["Bunny", "Buffalo", "Sheep", "Dragon", "Fox", "Lion", "Cat", "Raccoon", "Paula"]
JOBS = ["1st Job", "2nd Job", "3rd Job"]

CHR_FLAGS = {
    "Bunny":   [1, 512, 262144],
    "Buffalo": [2, 1024, 524288],
    "Sheep":   [4, 2048, 1048576],
    "Dragon":  [8, 4096, 2097152],
    "Fox":     [16, 8192, 4194304],
    "Lion":    [32, 16384, 8388608],
    "Cat":     [64, 32768, 16777216],
    "Raccoon": [124, 65536, 33554432],
    "Paula":   [256, 131072, 67108864]
}

SHOP_META = {
    "Bunny":   {"cat1": 128, "sex": 2, "type": 8},
    "Buffalo": {"cat1": 129, "sex": 1, "type": 8},
    "Sheep":   {"cat1": 130, "sex": 2, "type": 4},
    "Dragon":  {"cat1": 131, "sex": 1, "type": 4},
    "Fox":     {"cat1": 132, "sex": 2, "type": 2}, 
    "Lion":    {"cat1": 133, "sex": 1, "type": 2},
    "Cat":     {"cat1": 134, "sex": 2, "type": 1},
    "Raccoon": {"cat1": 135, "sex": 1, "type": 1},
    "Paula":   {"cat1": 128, "sex": 2, "type": 9}
}

def _fashion_detect_slot(name):
    n = name.lower()
    if any(x in n for x in ["hoodie", "vest", "blouse", "top", "tank", "t-shirt", "shirt", "coat", "jacket", "tunic", "robe", "dress", "suit", "t-neck", "turtleneck", "halter", "blazer", "shawl", "wrap", "protector"]):
        return 19, 43 # Top
    if any(x in n for x in ["jeans", "skort", "pants", "skirt", "shorts", "warmups", "slacks", "kilt"]):
        return 20, 44 # Bottom
    if any(x in n for x in ["shoes", "boots", "heels", "flats", "trainers", "loafers", "walkers", "airshoes"]):
        return 22, 46 # Shoes
    if any(x in n for x in ["gloves", "mittens", "paws", "armlets", "gauntlet", "wraps", "arm cover"]):
        return 21, 45 # Gloves
    if any(x in n for x in ["hat", "ribbon", "bow", "band", "collar", "hood tie", "brooch", "chou", "rubber", "necklace"]):
        return 18, 42 # Head / Face / Accessary
    if any(x in n for x in ["backpack", "sack", "satchel", "bag", "tote", "minisack", "cape"]):
        return 24, 48 # Cloak/Bag
    if any(x in n for x in ["belt", "sash"]):
        return 23, 47 # Belt
    if any(x in n for x in ["stockings", "socks"]):
        return 20, 44 # Sometimes socks are bottoms or shoes. Assigning bottom.
    if any(x in n for x in ["cane", "spellbook", "whip"]):
        return 27, 51 # Weapon/Accessory
    return 19, 43 # Default to Top

