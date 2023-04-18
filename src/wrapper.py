import parameters, precleaning, exposure, exposure_numba, observation, figures
from hmm import get_states, get_pi

def main():
    p = parameters.ask_params()
    startdate, enddate, countries, _, _, freq = p.get_params()

    def ask_use_numba():
        ask = input("Use numba ? Y/n > ").lower() or "y"
        if ask == "y":
            return (True, "-numba")
        elif ask == "n":
            return (False, "")
        else:
            return ask_use_numba()

    use_numba, numba_str = ask_use_numba()
   
    events = precleaning.get_events(p)

    def str_countries(countries):
        res = str(countries[0])
        for i in range(1, len(countries)):
            res += "-" + str(countries[i])
        return res

    if use_numba:
        print("\nComputing exposure to conventional warfare...")
        Ec = exposure_numba.get_exposure(events, "conventional", p, freq)
        print("Done !")

        print("\nSaved exposure to conventional warfare to " + f"../exposures/exposure{numba_str}_{str_countries(countries)}_conventional_{startdate}_{enddate}_{freq}.csv")
        Ec.to_csv(f"../exposures/exposure{numba_str}_{str_countries(countries)}_conventional_{startdate}_{enddate}_{freq}.csv")

        print("\nComputing exposure to terrorism...")
        Et = exposure_numba.get_exposure(events, "terrorism", p, freq)
        print("Done !")
       
        print("\nSaved exposure to terrorism to " + f"../exposures/exposure{numba_str}_{str_countries(countries)}_terrorism_{startdate}_{enddate}_{freq}.csv")
        Et.to_csv(f"../exposures/exposure{numba_str}_{str_countries(countries)}_terrorism_{startdate}_{enddate}_{freq}.csv")

    else:
        print("\nComputing exposure to conventional warfare...")
        Ec = exposure.get_exposure(events, "conventional", p, freq)
        print("Done !")

        print("\nSaved exposure to conventional warfare to " + f"../exposures/exposure{numba_str}_{str_countries(countries)}_conventional_{startdate}_{enddate}_{freq}.csv")
        Ec.to_csv(f"../exposures/exposure{numba_str}_{str_countries(countries)}_conventional_{startdate}_{enddate}_{freq}.csv")

        print("\nComputing exposure to terrorism...")
        Et = exposure.get_exposure(events, "terrorism", p, freq)
        print("Done !")
       
        print("\nSaved exposure to terrorism to " + f"../exposures/exposure{numba_str}_{str_countries(countries)}_terrorism_{startdate}_{enddate}_{freq}.csv")
        Et.to_csv(f"../exposures/exposure{numba_str}_{str_countries(countries)}_terrorism_{startdate}_{enddate}_{freq}.csv")


    print("\nComputing exposition to conventional warfare probabilities...")
    C = observation.get_probabilities(Ec)
    print("Done !")

    print("\nComputing exposition to terrorism probabilities...")
    T = observation.get_probabilities(Et)
    print("Done !")

    print(f"\nThe median of C is : {C.median().median()}")
    print(f"The median of T is : {T.median().median()}")

    m = float(input("Enter a value for m (default is 0.15) > ") or 0.15)
    xs = float(input("Enter a value for xs (default is 0.01) > ") or 0.01)

    print("\nComputing observations...")
    O = observation.get_observation(Et,Ec,C,T,m,xs)
    print("Done !")

    print("\nSaved observations to " + f"../observations/observation{numba_str}_{str_countries(countries)}_{startdate}_{enddate}_{freq}.csv")
    O.to_csv(f"../observations/observation{numba_str}_{str_countries(countries)}_{startdate}_{enddate}_{freq}.csv")

    pi = get_pi(countries[0])

    print("\nApplying Viterbi algorithm to estimate territorial control...")
    states_df = get_states(O, pi)
    print("Done !")
    
    print("\nSaved control to " + f"../controls/controls{numba_str}_{str_countries(countries)}_{startdate}_{enddate}_{freq}.csv")
    states_df.to_csv(f"../controls/controls{numba_str}_{str_countries(countries)}_{startdate}_{enddate}_{freq}.csv")


    print("\nCreating figures (in ../figures)...")
    figures.plot_control(figures.to_gdf(states_df.T), countries[0])
    print("Done !")


if __name__ == "__main__":
    main()
