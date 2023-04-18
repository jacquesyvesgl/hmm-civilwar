class Parameters:
    def __init__(self, ged_path, gtd_path, startdate, enddate, countries, perpetrators, h3_level, freq):
        self.ged_path = ged_path
        self.gtd_path = gtd_path
        self.startdate = startdate
        self.enddate = enddate
        self.countries = countries
        self.perpetrators = perpetrators
        self.h3_level = h3_level
        self.freq = freq

    def get_params(self):
        return (self.startdate, 
                self.enddate, 
                self.countries, 
                self.perpetrators, 
                self.h3_level, 
                self.freq)

def ask_params():
    ged_path = "../datasets/ged.csv"
    gtd_path = "../datasets/gtd.csv"

    def choose_country():
        # Note : on retourne la str dans une liste
        # car à la base le code prévoyait de gérer plusieurs pays d'un coup.
        # A modifier à l'avenir, peut-être...
        country = input("Choose a country : [I]raq | [N]igeria (default is Nigeria) > ").lower() or "n"
        if country=="n":
            return ["Nigeria"]
        elif country=="i":
            return ["Iraq"]
        else:
            return choose_country()

    countries = choose_country()
    
    startdate = input("Enter startdate (YYYY-MM-DD, default is 2008-01-01) > ") or "2008-01-01"
    enddate = input("Enter enddate (YYYY-MM-DD, default is 2019-12-31) > ") or "2019-12-31"

    perpetrators = []
    h3_level = int(input("Enter H3 level (0-15, default is 5) > ") or 5)

    freq = input("Enter frequency (default is M) > ") or "M"

    params = Parameters(ged_path, gtd_path, startdate, enddate, countries, perpetrators, h3_level, freq)

    return params

def main():
    p = ask_params()
    print(p)

if __name__ == "__main__":
    main()
