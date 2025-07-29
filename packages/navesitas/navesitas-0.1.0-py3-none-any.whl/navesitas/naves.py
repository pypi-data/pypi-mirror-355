class Naves:

    def __init__(self, brand, model, duration, link):
        self.brand = brand
        self.model = model
        self.duration = duration
        self.link = link

    def __repr__(self):
        return f"{self.brand} {self.model} [{self.duration} Segundos] ({self.link})"

naves = [
    Naves("Toyota", "Supra", 15, "https://www.youtube.com/shorts/igUFXRaosYc"),
    Naves("Nissan", "GT-R R35", 10, "https://www.youtube.com/shorts/S9cU_1cj03Y"),
    Naves("Lamborghini", "Aventador SVJ", 5, "https://www.youtube.com/shorts/w0o_a6KTjAc")
]

def list_naves():
    for nave in naves:
        print(nave)

def search_nave_by_brand(brand):
    for nave in naves:
        if nave.brand == brand:
            return nave

    return None
