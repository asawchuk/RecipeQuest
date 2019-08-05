# RecipeQuest
A simple program to accept ingredients from a user and use them to search food2fork.com for tasty recipes!

## Dependencies
In order to run this program, you need to make sure you have python 2.7 interpreter installed.  Additionally, there are a couple other non-builtin packages that will need to be installed.  See below for details.

To run the main program, the python package **requests** must be installed, which can be done using the following command:  
`pip install requests`

Further, in order to run the unit tests, the additional python packages **pytest** and **mock** will need to be installed:  
`pip install pytest mock`

## Running RecipeQuest
Before running the program, you will need to get an API key from food2fork.com.  To do so, navigate to http://www.food2fork.com and create an account.  Then, go to the "Browse" top menu, and click "Recipe API".  You will see your API key on this screen.  Copy this API key and paste it into the appropriate place in the file **config.py** after you've cloned this repository.

Once your API key is configured, to run the program, simply execute it with your python 2.7 interpreter:  
`python RecipeQuest.py`

## Running the unit tests
To run the unit tests, run the pytest command in the directory containing the **test_RecipeQuest.py** file:  
`pytest`

## Caveats
There are a couple caveats that should be taken into consideration when using this program:
* The original goal of this program was to accept ingredients from the user and use them to search for the most popular recipe containing all of the supplied ingredients.  The food2fork API has two ways of sorting--by rank, or by trendingness.  While these could both potentially be a measure of popularity, it could be argued that the trendingness is a more accurate measure.  Unfortunately, it appears that as of late (at least during 8/2/19 - 8/5/19), the ability to sort results by trendingness is not functioning, as it will instead return an empty set of recipes.  That said, this program will instead use the highest-ranked recipe from the list returned by the search query.

* One of the features of this program is that it will tell the user what ingredients he or she is missing in order to prepare the discovered recipe.  In making the comparison between the ingredients entered by the user and those in the recipe, this version of the program simply uses a substring-based approach to determine whether or not a recipe ingredient matches one that the user has.  In some cases, this may be inaccurate, for example, if a stocked ingredient is "pepper", which could match recipe ingredients "black pepper" or "green peppers".  This is an area for improvement in a future version.
