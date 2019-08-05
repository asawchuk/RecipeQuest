import requests
import urllib
import json
import config

"""
A simple program to accept ingredients from a user and use them to search food2fork.com for tasty recipes!
"""

search_url = 'https://www.food2fork.com/api/search'
recipe_url = 'https://www.food2fork.com/api/get'
sort_pattern_rating = 'r'
sort_pattern_trendiness = 't'

class RecipeQuest(object):
    """The main class for RecipeQuest.  This gathers and stores the ingredients which the user
    already has in stock."""
    def __init__(self):
        self.user_ingredients = []

    # Gather the list of ingredients from the user
    def prompt_user_for_ingredients(self):
        """Prompt the user for ingredients he or she already has in stock."""
        self.user_ingredients = []
        ingredient_in = ''
        print 'Please enter the ingredients you have, with commas in between each ingredient.'
        # while True:
        ingredients_in = raw_input('Ingredients (comma-separated): ')
        if not ingredients_in.strip():
            print('ERROR: No ingredients entered!')
            return False
        ingredients = ingredients_in.split(',')
        for ingredient in ingredients:
            ingredient = ingredient.strip()
            if ingredient:
                self.user_ingredients.append(ingredient)
        return True

    def get_user_ingredients(self):
        """Retrieve the list of ingredients specified by the user that he or she already has."""
        return self.user_ingredients


class RESTAPI(object):
    """This class is used to perform interactions with food2fork's REST API.  Note that the API
    key is not stored here, but instead supplied by a separate config.py file."""
    def __init__(self, api_key):
        self.api_key = api_key

    def build_url(self, base_url, params):
        """Build the complete URL for initiating a transaction with the REST API, including
        the base URL for the API endpoint, the API key, and the rest of the query parameters
        needed to complete the transaction.  Any characters within the query parameters will
        also be URL-encoded (e.g., using the percent-encoding scheme, like '%2E') as needed.

        Keyword arguments:
        base_url -- the base URL for the API endpoint
        params -- a dict of query parameters and their values
        """
        url_substr_list = [base_url, '?key=', self.api_key]
        for param, value in params.iteritems():
            encoded_value = urllib.quote(str(value))
            url_substr_list.append('&')
            url_substr_list.extend([param, '=', encoded_value])
        return ''.join(url_substr_list)

    def make_request(self, base_url, params):
        """Build the URL for the transaction and then use it to make the HTTP request to
        the REST API endpoint.

        Keyword arguments:
        base_url -- the base URL for the API endpoint
        params -- a dict of query parameters and their values
        """
        url = self.build_url(base_url, params)
        resp = requests.get(url)
        content = resp.content
        if resp.status_code != 200:
            print('ERROR: Error while making request to server (HTTP code: ' + str(resp.status_code) + ')')
            return ''
        if len(content) == 0:
            print('ERROR: No response body from HTTP request')
        return content


class Recipe(object):
    """Contains the attributes and operations associated with a particular recipe.

    Attributes:
    rId -- recipe identifier associated with this recipe
    title -- the name of the recipe
    f2f_url -- the URL to retrieve this recipe on food2fork in a web browser
    ingredients -- a list of ingredients for this recipe, where each ingredient is a string
    """
    def __init__(self, rId):
        self.rId = rId
        self.title = ''
        self.f2f_url = ''
        self.ingredients = []

    def lookup_ingredients(self):
        """For a given recipe which has been instantiated with a valid rId, this will use
        the REST API to retrieve the rest of the details regarding the recipe, including
        the ingredients, the title, and the URL on the food2fork website."""
        recipe_params = {'rId': self.rId}
        api = RESTAPI(config.api_key)
        full_recipe_json = api.make_request(recipe_url, recipe_params)
        if len(full_recipe_json) == 0:
            return False

        # Parse the JSON response to get the recipe ingredients
        try:
            full_recipe = json.loads(full_recipe_json)
        except ValueError:
            print('ERROR: JSON decoding failed!')
            return False
        if type(full_recipe) is not dict:
            print('ERROR: Unexpected type (not object) of JSON for full recipe')
            return False
        # Error out only if 'recipe' or 'ingredients' not found -- 'title' and 'f2f_url' optional
        if 'recipe' in full_recipe and 'ingredients' in full_recipe['recipe']:
            self.ingredients = full_recipe['recipe']['ingredients']
        else:
            print('ERROR: Recipe response in unexpected format!')
            return False
        if 'title' in full_recipe['recipe']:
            self.title = full_recipe['recipe']['title']
        if 'f2f_url' in full_recipe['recipe']:
            self.f2f_url = full_recipe['recipe']['f2f_url']
        return True

    def compute_missing_ingredients(self, stocked_ingredients):
        """This will compare the ingredients that are provided to the method to the
        ingredients known to be required by the recipe, and will return any ingredients that
        are in the recipe but not supplied as a stocked ingredient.

        Note that this function makes an assumption for comparing ingredients: if a stocked
        ingredient exists as a substring of the recipe's ingredient, then it is considered a
        match and not a 'missing ingredient'.  In some cases, this may be inaccurate, for example,
        if a stocked ingredient is 'pepper', which could match recipe ingredients 'black pepper' or
        'green peppers'.

        Keyword arguments:
        stocked_ingredients -- a list of strings representing the ingredients that the user already
                               has in stock
        """
        missing_ingredients = []
        for recipe_ingredient in self.ingredients:
            have_ingredient = False
            for my_ingredient in stocked_ingredients:
                # Making an assumption here that if our ingredient exists as a substring of the
                # recipe's ingredient, then it's a match and we have that ingredient.  Note that
                # this could be dangerous, for example, if the user enters 'pepper', that could
                # match recipe ingredients 'black pepper' or 'green peppers'.
                if my_ingredient in recipe_ingredient:
                    have_ingredient = True

            if not have_ingredient:
                missing_ingredients.append(recipe_ingredient)

        return missing_ingredients

    def get_title(self):
        """Get and return the title of the recipe."""
        return self.title

    def get_f2f_url(self):
        """Get and return the food2fork URL of the recipe."""
        return self.f2f_url


def parse_recipe_list(recipe_list_json):
    """Helper function to parse the JSON response of a search query into a dict.

    Keyword arguments:
    recipe_list_json -- a JSON representation of the list of recipes returned
                        from a search query
    """
    try:
        recipes = json.loads(recipe_list_json)
    except ValueError:
        print('ERROR: JSON decoding failed!')
        return []
    if type(recipes) is not dict:
        print('ERROR: Unexpected type (not object) of JSON for recipes list')
        return []
    return recipes


def find_recipes(ingredients, sort_pattern=sort_pattern_rating):
    """Helper function to construct, perform, and process the results of a search, given
    specific ingredients.

    Keyword arguments:
    ingredients -- a list of ingredients as strings used to search for recipes
    sort_pattern -- the pattern by which the results should be sorted ('r' is default,
                    for sorting by rank)
    """
    api = RESTAPI(config.api_key)
    page_number = 1
    search_params = {'q': ','.join(ingredients),
                     'sort': sort_pattern,
                     'page': page_number}
    recipes_json = api.make_request(search_url, search_params)
    if len(recipes_json) == 0:
        print('ERROR: No response received from search!')
        return []
    recipes = parse_recipe_list(recipes_json)
    return recipes


if __name__ == '__main__':
    rq = RecipeQuest()

    # First get the ingredients from the user
    if not rq.prompt_user_for_ingredients():
        exit(1)
    print('\nSearching for recipes including the following ingredients:')
    print('  ' + ', '.join(rq.get_user_ingredients()) + '\n')

    # Do a recipe search with those user entered ingredients
    # Note that sorting for 't' (trandingness) appears to be broken (as of 8/2/19 - 8/5/19),
    # so we will just use the 'r' (rank) sorting method for now.  The 't' sort method simply
    # returns a body with content '{"count": 0, "recipes": []}'.
    recipes_list = find_recipes(rq.get_user_ingredients())

    # Find the first (highest-rated) recipe from the search results
    first_recipe_id = ''
    if 'recipes' not in recipes_list:
        print('ERROR: Unexpected format of search results!')
        exit(1)
    num_recipes = len(recipes_list['recipes'])
    if num_recipes == 0:
        print('No recipes found!')
        exit(0)
    print('Found ' + str(num_recipes) + ' recipes, getting the highest-rated one...')
    first_recipe = recipes_list['recipes'][0]
    if 'recipe_id' not in first_recipe:
        print('ERROR: Unable to find recipe_id in recipe!')
        exit(1)
    first_recipe_id = first_recipe['recipe_id']
    recipe = Recipe(first_recipe_id)

    # Now that we have the recipe, get the ingredients from the full recipe info
    if not recipe.lookup_ingredients():
        print('ERROR: Unable to find ingredients for recipe!')
        exit(1)

    # Print out the recipe name, URL, and the ingredients that the user needs for this recipe
    print('\nRecipe:  ' + recipe.get_title())
    print('URL:     ' + recipe.get_f2f_url())
    missing_ingredients = recipe.compute_missing_ingredients(rq.get_user_ingredients())
    if not missing_ingredients:
        print('You have all the ingredients you need to cook this recipe!')
    else:
        print('Additional ingredients you need to cook this recipe:')
        for ingredient in missing_ingredients:
            print('  ' + ingredient)
