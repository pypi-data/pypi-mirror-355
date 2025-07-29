# kudet/model_utils.py

def calculate_features(car_dict):
    """
    Araç özelliklerini sayısal değerlere dönüştüren örnek fonksiyon.
    Bu fonksiyon daha sonra model girişini oluşturmak için kullanılacaktır.
    """
    features = [
        car_dict.get("yıl", 2015),
        car_dict.get("kilometre", 100000),
        1 if car_dict.get("vites") == "otomatik" else 0,
        1 if car_dict.get("yakıt") == "dizel" else 0
    ]
    return features

