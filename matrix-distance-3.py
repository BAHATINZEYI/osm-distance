# %%
# Libraries
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import tqdm 
import pandas as pd 
import os

# %%
# Constants
SRC_PATH = "/Users/abdoul/Desktop/Training/OSM-distance"
RESULTS_PATH = os.path.join(SRC_PATH, 'resultats.csv')

# %%
# Function to calculate the distance and duration between two points using the OpenStreetMap API
def get_osrm_route_info(profile, lat1, lon1, lat2, lon2):

    osrm_endpoint = "http://router.project-osrm.org/route/v1/{}/{},{};{},{}?geometries=geojson&steps=true"
    response = requests.get(osrm_endpoint.format(profile, lon1, lat1, lon2, lat2))

    if response.status_code == 200: # The HTTP 200 OK success status response code indicates that the request has succeeded
        data = response.json()
        if "routes" in data and len(data["routes"]) > 0:
            route = data["routes"][0]
            distance = route["distance"] / 1000  # Convert meters to kilometers
            duration = route["duration"] / 60  # Convert seconds to minutes
            return distance, duration
        else:
            return None, None
    else:
        return None, None

# %%
# Define the profiles, origins, and destinations

origins = destinations = pd.read_csv("./coord_IRIS.csv").values[:10]

profiles = ["car"]

# Create resultat file
with open(RESULTS_PATH, "w") as f:
    f.write("profile,origin,destination,distance,duration\n")

# %%
def get_osrm_matrix_parallel(profiles: list, origins: list, destinations: list):
    """
    Calcule en parallèle les distances et durées entre chaque origine et destination
    pour chaque profil, en utilisant la fonction get_osrm_route_info.
    
    :param profiles: Liste des profils à utiliser.
    :param origins: Liste d'éléments de la forme (origine, lat, lon).
    :param destinations: Liste d'éléments de la forme (destination, lat, lon).
    :return: Dictionnaire où chaque profil est associé à une liste de résultats.
    """
    
    # Fonction qui traite une seule combinaison de profil, origine et destination
    def process_task(profile, item1, item2):
        origin, lat1, lon1 = item1[0], item1[1], item1[2]
        destination, lat2, lon2 = item2[0], item2[1], item2[2]

        if origin == destination:
            distance, duration = 0, 0 
        else:
            distance, duration = get_osrm_route_info(profile, lat1, lon1, lat2, lon2)
            if distance is not None and duration is not None:
                distance = round(distance, 2)
            else:
                print(f"Erreur lors de la récupération des infos de route pour {profile}")
        
        with open(RESULTS_PATH, "a") as f:
            f.write(f"{profile},{origin},{destination},{distance},{duration}\n")
            
    # Constitution de la liste des tâches à exécuter
    tasks = []
    for profile in profiles:
        print(f"Calcul des distances en utilisant le profil : {profile}")
        for item1 in origins:
            for item2 in destinations:
                tasks.append((profile, item1, item2))
                
    total_tasks = len(tasks)
    
    # Exécution parallèle des tâches
    with ThreadPoolExecutor(max_workers=(os.cpu_count() - 1)) as executor:
        futures = [executor.submit(process_task, profile, item1, item2)
                   for profile, item1, item2 in tasks]
        
        with tqdm.tqdm(total=total_tasks) as pbar:
            for future in as_completed(futures):
                future.result()
                pbar.update(1)

# %%
# raw_data = get_osrm_matrix_parallel(profiles, origins, destinations)
get_osrm_matrix_parallel(profiles, origins, destinations)


# %%
# Distance matrix
df = pd.read_csv(RESULTS_PATH)
df_distance = df.pivot(index="origin", columns="destination", values="distance")
df_distance.to_csv(f"{SRC_PATH}/distance_matrix.csv")

# %%
# Duration matrix
df = pd.read_csv(RESULTS_PATH)
df_duration = df.pivot(index="origin", columns="destination", values="duration")
df_duration.to_csv(f"{SRC_PATH}/duration_matrix.csv")


