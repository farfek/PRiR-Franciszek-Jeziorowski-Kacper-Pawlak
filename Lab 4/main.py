import argparse
import random
import time
from concurrent.futures import ProcessPoolExecutor

def fitness(kolejnosc, czasy):
    koniec = [0] * len(czasy[0])
    for zadanie in kolejnosc:
        koniec[0] += czasy[zadanie][0]
        for m in range(1, len(koniec)):
            koniec[m] = max(koniec[m], koniec[m - 1]) + czasy[zadanie][m]
    return koniec[-1]

def podziel(populacja, n):
    rozmiar, reszta = divmod(len(populacja), n)
    fragmenty = []
    start = 0
    for i in range(n):
        koniec = start + rozmiar + (i < reszta)
        fragmenty.append(populacja[start:koniec])
        start = koniec
    return fragmenty

def ocen_fragment(dane):
    fragment, czasy = dane
    return [fitness(osobnik, czasy) for osobnik in fragment]

def krzyzowanie(a, b, los):
    n = len(a)
    lewy, prawy = sorted(los.sample(range(n), 2))
    dziecko = [-1] * n
    dziecko[lewy:prawy] = a[lewy:prawy]
    zajete = set(a[lewy:prawy])
    brakujace = [x for x in b[prawy:] + b[:prawy] if x not in zajete]
    for i, zadanie in enumerate(brakujace):
        dziecko[(prawy + i) % n] = zadanie
    return dziecko

def nastepne_pokolenie(populacja, oceny, los):
    ranking = sorted(range(len(populacja)), key=lambda i: oceny[i])
    nowa = [populacja[i].copy() for i in ranking[:2]]  # Dwie elity.

    def wybierz():
        kandydaci = los.sample(range(len(populacja)), 3)
        return min(kandydaci, key=lambda i: oceny[i])

    while len(nowa) < len(populacja):
        a, b = wybierz(), wybierz()
        while b == a:
            b = wybierz()
        dziecko = (krzyzowanie(populacja[a], populacja[b], los)
                   if los.random() < 0.9 else populacja[a].copy())
        if los.random() < 0.15:
            i, j = los.sample(range(len(dziecko)), 2)
            dziecko[i], dziecko[j] = dziecko[j], dziecko[i]
        nowa.append(dziecko)
    return nowa

def algorytm(args, tryb, procesy=0):
    # Ten sam seed = identyczna instancja i identyczna populacja startowa.
    los = random.Random(123)
    czasy = [[los.randint(10, 100) for _ in range(args.machines)]
             for _ in range(args.jobs)]
    populacja = [los.sample(range(args.jobs), args.jobs)
                 for _ in range(args.population)]

    start = time.perf_counter()
    czas_oceny = 0.0
    pula = None
    najlepszy = float("inf")
    poczatkowy = None

    try:
        if tryb == "parallel":
            pula = ProcessPoolExecutor(max_workers=procesy)

        for pokolenie in range(args.generations + 1):
            t0 = time.perf_counter()
            if tryb == "serial":
                oceny = [fitness(x, czasy) for x in populacja]
            elif tryb == "parallel":
                fragmenty = podziel(populacja, procesy)
                wyniki = pula.map(ocen_fragment, [(x, czasy) for x in fragmenty])
                oceny = [wartosc for grupa in wyniki for wartosc in grupa]
            czas_oceny += time.perf_counter() - t0

            if pokolenie == 0:
                poczatkowy = min(oceny)
            najlepszy = min(najlepszy, min(oceny))
            if pokolenie < args.generations:
                populacja = nastepne_pokolenie(populacja, oceny, los)
    finally:
        if pula is not None:
            pula.shutdown()

    czas_calkowity = time.perf_counter() - start
    return czas_oceny, czas_calkowity, poczatkowy, najlepszy

def porownanie(args):
    warianty = [
        ("Sekwencyjny", "serial", 0),
        ("Rownolegly 2 procesy", "parallel", 2),
        ("Rownolegly 4 procesy", "parallel", 4),
        ("Rownolegly 6 procesy", "parallel", 6),
        ("Rownolegly 8 procesy", "parallel", 8),
    ]
    print(f"Zadania: {args.jobs}, maszyny: {args.machines}, "
          f"populacja: {args.population}, pokolenia: {args.generations}")
    print(f"\n{'Tryb':<24} {'Ocena [s]':>12} {'Calkowity [s]':>16} {'Wynik GA':>12}")
    print("-" * 68)
    for nazwa, tryb, n in warianty:
        ocena, caly, przed, po = algorytm(args, tryb, n)
        print(f"{nazwa:<24} {ocena:>12.3f} {caly:>16.3f} {po:>12}", flush=True)

    print("\nOcena [s] = suma czasu obliczania funkcji celu dla populacji.")
    print("Calkowity [s] = czas algorytmu wraz z uruchomieniem puli procesow.")
    print("Wynik GA = Cmax, wartosc funkcji celu; nie jest to czas dzialania Pythona.")


def main():
    parser = argparse.ArgumentParser(description="GA: porownanie czasow w sekundach")
    parser.add_argument("--jobs", type=int, default=400)
    parser.add_argument("--machines", type=int, default=20)
    parser.add_argument("--population", type=int, default=180)
    parser.add_argument("--generations", type=int, default=30)
    parser.add_argument("polecenie", nargs="?", choices=["run"], default="run")
    parser.add_argument("--mode", choices=["all"], default="all", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.jobs < 2 or args.machines < 2 or args.population < 4 or args.generations < 1:
        parser.error("Wymagane: jobs>=2, machines>=2, population>=4, generations>=1")
    porownanie(args)

if __name__ == "__main__":
    main()  # Wymagane na Windows przy ProcessPoolExecutor.
