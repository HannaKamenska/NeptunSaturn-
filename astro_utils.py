import swisseph as swe

# Планеты
PLANETS = [
    swe.SUN,
    swe.MOON,
    swe.MERCURY,
    swe.VENUS,
    swe.MARS,
    swe.JUPITER,
    swe.SATURN,
    swe.URANUS,
    swe.NEPTUNE,
    swe.PLUTO,
]

PLANET_NAMES = {
    swe.SUN: "Солнце",
    swe.MOON: "Луна",
    swe.MERCURY: "Меркурий",
    swe.VENUS: "Венера",
    swe.MARS: "Марс",
    swe.JUPITER: "Юпитер",
    swe.SATURN: "Сатурн",
    swe.URANUS: "Уран",
    swe.NEPTUNE: "Нептун",
    swe.PLUTO: "Плутон",
}

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]

ASPECTS = {
    0: "соединение",
    60: "секстиль",
    90: "квадрат",
    120: "тригон",
    180: "оппозиция"
}

ORBIS = {
    "Солнце": 10,
    "Луна": 9,
    "Меркурий": 5,
    "Венера": 5,
    "Марс": 5,
    "Юпитер": 7,
    "Сатурн": 5,
    "Уран": 5,
    "Нептун": 5,
    "Плутон": 5
}

def get_zodiac_sign(degree):
    sign = int(degree // 30)
    return ZODIAC_SIGNS[sign % 12]

def get_house_number(degree, house_cusps):
    for i in range(12):
        start = house_cusps[i]
        end = house_cusps[(i + 1) % 12]
        if start < end:
            if start <= degree < end:
                return i + 1
        else:
            if degree >= start or degree < end:
                return i + 1
    return 0

def calculate_planet_positions(jd):
    positions = {}
    for planet in PLANETS:
        pos, _ = swe.calc_ut(jd, planet)
        positions[PLANET_NAMES[planet]] = pos[0]
    return positions

def calculate_houses(jd, lat, lon):
    houses, ascmc = swe.houses(jd, lat, lon, b'P')
    return {
        "Asc": ascmc[0],
        "MC": ascmc[1],
        "Houses": houses.tolist() if hasattr(houses, 'tolist') else list(houses)
    }

def calculate_aspects(planets: dict, houses: dict) -> list:
    aspects = []
    aspect_angles = {
        "соединение": 0,
        "оппозиция": 180,
        "тригон": 120,
        "квадрат": 90,
        "секстиль": 60
    }
    orb_limits = {
        "Солнце": 10, "Луна": 9, "Юпитер": 7, "Сатурн": 5,
        "Меркурий": 5, "Венера": 5, "Марс": 5, "Уран": 5,
        "Нептун": 5, "Плутон": 5
    }
    names = list(planets.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            p1, p2 = names[i], names[j]
            deg1, deg2 = planets[p1], planets[p2]
            diff = abs(deg1 - deg2)
            diff = 360 - diff if diff > 180 else diff
            for asp_name, asp_angle in aspect_angles.items():
                orb = max(orb_limits.get(p1, 5), orb_limits.get(p2, 5))
                if abs(diff - asp_angle) <= orb:
                    aspects.append(f"{p1} {asp_name} {p2} ({diff:.2f}°)")
    return aspects

def calculate_aspects(planets: dict, houses: dict):
    aspects = []
    names = list(planets.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            name1, name2 = names[i], names[j]
            pos1, pos2 = planets[name1], planets[name2]
            diff = abs(pos1 - pos2)
            if diff > 180:
                diff = 360 - diff

            for angle, label in ASPECTS.items():
                if abs(diff - angle) < 10:
                    orb1 = ORBIS.get(name1, 5)
                    orb2 = ORBIS.get(name2, 5)
                    max_orb = max(orb1, orb2)

                    same_sign = int(pos1 // 30) == int(pos2 // 30)
                    through_sign = int(pos1 // 30) != int(pos2 // 30)
                    reduced_orb = max_orb
                    if angle == 0 and through_sign:
                        reduced_orb = max_orb / 2
                    elif angle != 0 and through_sign:
                        reduced_orb = max_orb * 0.7

                    orb = abs(diff - angle)
                    if orb <= reduced_orb:
                        aspects.append(
                            f"{name1} {label} {name2} ({diff:.2f}°, орб {orb:.2f}° из допустимых {reduced_orb:.1f}°)"
                        )
    return aspects
