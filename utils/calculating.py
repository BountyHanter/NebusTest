# Функция для расчёта расстояния между точками (Haversine formula)
import math


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Радиус Земли в километрах
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c  # Расстояние в километрах
