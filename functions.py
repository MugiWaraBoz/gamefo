import string
import requests
import random
from datetime import date



def check_password(password):
    requirements_list = []

    if len(password) >= 8:
        has_alpha = any(char.isalpha() for char in password)
        if has_alpha:
            requirements_list.append("Password has at least one letter")
            
            has_digit = any(char.isdigit() for char in password)
            if has_digit:
                requirements_list.append("Password has at least one number")
                
                has_punct = any(char in string.punctuation for char in password)
                if has_punct:
                    requirements_list.append("Password has unique characters")
                    requirements_list.append("All requirements passed!")
                else:
                    requirements_list.append("Password doesn't have unique characters")
                    
            else:
                requirements_list.append("Password doesn't have a number")
                
        else:
            requirements_list.append("Password doesn't have a letter")
            
    else:
        requirements_list.append("Password needs to be at least")
        requirements_list.append("8 characters long")

    return requirements_list



# api fetching
api_key_rawg = "Your API from RAWG API"
baseURL = "https://api.rawg.io/api/"

def game_data(game_name):
    endPoint = "games"
    params = {
        "page_size": 16,  # Adjust as needed
        "search": game_name,
        "search_precise": False,
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        games = data.get("results", [])
        return games, data
    else:
        print(f"Error: {response.status_code}")
        return None



def per_game_detail(game_id):
    endPoint = f"games/{game_id}"
    endPoint_ss = f"games/{game_id}/screenshots"
    endPoint_dlc = f"games/{game_id}/additions"
    params = {
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)
    response_ss = requests.get(baseURL + endPoint_ss, params=params)
    response_dlc = requests.get(baseURL + endPoint_dlc, params=params)

    if response.status_code == 200:
        data = response.json()
        if response_ss.status_code == 200:
            screenshots = response_ss.json()
            if response_dlc.status_code == 200:
                dlcs = response_dlc.json()
                return data, screenshots, dlcs
            return data, screenshots
        return data
    else:
        return None
    
    
    
def top_10_ranked_games():
    endPoint = "games"
    params = {
        "page_size": 10,  # Adjust as needed
        "ordering": "-rating, -ratings_count, -suggestions_count",
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        games = data.get("results", [])
        return games
    else:
        print(f"Error: {response.status_code}")
        return None


start_year = date.today().year
end_date = date.today().strftime("%Y-%m-%d")
def top_released_games_this_year():
    endPoint = "games"
    params = {
        "dates": f"{start_year}-01-01,{end_date}",
        "page_size": 10,  # Adjust as needed
        "ordering": "-rating, -ratings_count, -suggestions_count, -metacritic",
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        games = data.get("results", [])
        return games
    else:
        print(f"Error: {response.status_code}")
        return None
    
    
def get_genres():
    endPoint = "genres"
    params = {
        "page_size": 20,
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        genres = data.get("results", [])
        return genres
    else:
        print(f"Error: {response.status_code}")
        return None

    
    
def get_tags():
    endPoint = "tags"
    params = {
        "page_size": 40,
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        tags = data.get("results", [])
        return tags
    else:
        print(f"Error: {response.status_code}")
        return None
    



# do a 8 platform call
def get_platforms():
    endPoint = "platforms"
    params = {
        "page_size": 8,
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        platf = data.get("results", [])
        return platf
    else:
        print(f"Error: {response.status_code}")
        return None



# do a 10 publishers call
def get_publishers():
    endPoint = "publishers"
    params = {
        "page_size": 10,
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        pub = data.get("results", [])
        return pub
    else:
        print(f"Error: {response.status_code}")
        return None


def get_total_games():
    endPoint = "games"
    params = {
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        total_count = data['count']
        return total_count
    else:
        print(f"Error: {response.status_code}")
        return None


# do a 10 developers call
def get_developers():
    endPoint = "developers"
    params = {
        "page_size": 10,
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)


    if response.status_code == 200:
        data = response.json()
        dev = data.get("results", [])
        return dev
    else:
        print(f"Error: {response.status_code}")
        return None


def filter_game(genres, tags, platforms, publishers, developers, order):
    endPoint = "games"
    params = {
        "page_size": 16,
        "key": api_key_rawg  # Add the API key to the parameters
    }
    
    # Include order in the request only if it's not empty
    if order:
        params["ordering"] = order
        
    # Include genres in the request only if it's not empty
    if genres:
        params["genres"] = genres

    # Include tags in the request only if it's not empty
    if tags:
        params["tags"] = tags
    
    # Include platforms in the request only if it's not empty
    if platforms:
        params["platforms"] = platforms
    
    # Include publishers in the request only if it's not empty
    if publishers:
        params["publishers"] = publishers
    
    # Include developers in the request only if it's not empty
    if developers:
        params["developers"] = developers

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        games = data.get("results", [])
        return games, data
    else:
        print(f"Error: {response.status_code}")
        return None
   
   
    
def get_recommandation(genres, devs, pubs, order, plat):
    endPoint = "games"
    
    params = {
        "page_size": 16,
        "key": api_key_rawg  # Add the API key to the parameters
    }
    
    # Include order in the request only if it's not empty
    if order:
        params["ordering"] = order
        
    # Include genres in the request only if it's not empty
    if genres:
        params["genres"] = genres

    # Include devs in the request only if it's not empty
    if devs:
        params["developers"] = devs
    
    # Include pubs in the request only if it's not empty
    if pubs:
        params["publishers"] = pubs
    
    # Include pubs in the request only if it's not empty
    if plat:
        params["platforms"] = plat

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        total_count = data['count']
        total_page = -(-total_count // 16)
        randomPage = random.randint(0, total_page)
        
        params["page"] = randomPage
        
        response2nd = requests.get(baseURL + endPoint, params=params)
        data2nd = response2nd.json()
        games = data2nd.get("results", [])
        if games:
            return games
        else:
            # If the page has no data, recursively call the function again
            return get_recommandation(genres, devs, pubs, order, plat)
        
    
    else:
        print(f"Error: {response.status_code}")
        return None


def advanced_game_randomizer(genres, devs, pubs, plat , order):
    endPoint = "games"
    
    params = {
        "page_size": 40,
        "key": api_key_rawg  # Add the API key to the parameters
    }
    
    # Include order in the request only if it's not empty
    if order:
        params["ordering"] = order
        
    # Include genres in the request only if it's not empty
    if genres:
        params["genres"] = genres

    # Include devs in the request only if it's not empty
    if devs:
        params["developers"] = devs
    
    # Include pubs in the request only if it's not empty
    if pubs:
        params["publishers"] = pubs
    
    # Include pubs in the request only if it's not empty
    if plat:
        params["platforms"] = plat

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        
        total_count = data['count']
        total_page = -(-total_count // 40)
        randomPage = random.randint(0, total_page)      
        
        params["page"] = randomPage
        
        response2nd = requests.get(baseURL + endPoint, params=params)
        data2nd = response2nd.json()
        
        games = data2nd.get("results", [])
        
        if games:
            random_number_for_game_id = random.randint(0, len(games) - 1)
            game_id = games[random_number_for_game_id]['id']
            return game_id
        else:
            # If the page has no data, recursively call the function again
            return advanced_game_randomizer(genres, devs, pubs, plat, order)
    
    else:
        print(f"Error: {response.status_code}")
        return None
    
    
     
def genre_game_detail(genre_id):
    endPoint = "games"
    params = {
        "genres": genre_id,
        "key": api_key_rawg  # Add the API key to the parameters
    }

    response = requests.get(baseURL + endPoint, params=params)

    if response.status_code == 200:
        data = response.json()
        games = data.get("results", [])
        return games, data
    else:
        print(f"Error: {response.status_code}")
        return None


    
    
# another api call for quotes!
# https://www.ultima.rest/
# 100req per hour
def get_random_quote():
    url = "https://www.ultima.rest/api/random"

    response = requests.get(url)

    if response.status_code == 200:
        quote = response.json()
        return quote
    else:
        print(f"Error: {response.status_code}")
        return None
