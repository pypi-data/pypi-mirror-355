# Notes

## Plan

improvements

- detailed review of AI written docs - some things need fixing!
  - move references to papers to docs - all should be in docs. Only one in README should be the main one.
  - index
    - some links broken - eg link to research in concepts
  - quickstart
    - example 3 - use the CSVAdapter?
  - cli
    - add note that the output includes lots of HTML!
    - confabulation of extra env vars - should we just implement them?
    - algorithm comparison again - link to canonical place
    - check the error messages
  - adapters
    - lots of code examples - are they actually decent? Better to fix or delete?
  - advanced
    - lots of code examples - are they actually decent? Better to fix or delete?
  - missing completely
    - min_flex, max_flex -> advanced?
- set up stuff for pypi publishing
- review TODO comments
- more tests
  - CLI - see <https://click.palletsprojects.com/en/stable/testing/>
- change output and `_print()` to use logging?
- selection code improvements

  - abstract class for interface - dict to call them?
  - more tests?

- show to Nick and Brett

  - is there a reason to require exactly 0 or 2 address columns? Why not 1 or 3?

- convert strat app to use it (?)
- point Paul Golz and others at it

## Done

- project set up
- settings code copied from refactor
- feature reading code copied from refactor
- ask LLM to write more unit tests for existing code
- people reading code
- selection code using feature and people objects
  - household/committee stuff
  - legacy first
  - other algs later
- selection code improvements
  - split out functions to reduce complexity of large functions
    - look for repeated code that is _semantically_ the same, not just happens to look the same
    - think hard about a good name for the new function. If a single name can't apply to multiple uses then ask me if I think one function should serve both uses
- move code about a bit
  - ~~all from `find_sample.py` to `committee_generation.py`~~
  - move the high level `find_random_sample()` to a new module - `core.py`
- add `run_stratification` to core
- `_get_selected_people_lists()`
  - 2 branches - one for multiple assembly selection, one for single assembly -> split into 2 functions
  - multiple assemblies - just the person ids for each assembly. One assembly is one column. Remaining rows is blank, so can drop that.
  - single assembly
    - selected - one row per person
      - then deletes those selected (and those at same address as required)
    - remaining is those left after above deletions - again, one row per person
  - then call `_output_selected_remaining()` with `settings, selected, remaining`
- add `csv` and `gsheet` modules - think about design so that core code does not know about them
  - wrap with CSV and GSheet stuff
- get old e2e tests, adapt them for the new world
- Remove JSON fine from main settings, only use for gsheet version
- move to `secrets` - but we want to do `random.seed()` - so will need to do something about that.
- add CLI? CSV only? Or Gsheet too? Could also have things like "generate sample data"
  - CLI with optional dependency click
- docs folder

## old code class/method/function list

### Still to migrate

```python
class PeopleAndCats:
    def people_cats_run_stratification(self, settings: Settings, test_selection: bool):
    def _get_selected_people_lists(self, settings: Settings):

class PeopleAndCatsCSV(PeopleAndCats):
    def __init__(self):
    def get_selected_file(self):
    def get_remaining_file(self):
    def load_cats(self, file_contents, dummy_category_tab, settings: Settings):
    def load_people():
    def _output_selected_remaining():

class PeopleAndCatsGoogleSheet(PeopleAndCats):
    def __init__(self):
    def _tab_exists(self, tab_name):
    def _clear_or_create_tab(self, tab_name, other_tab_name, inc):
    def load_cats(self, g_sheet_name, category_tab_name, settings: Settings):
    def load_people():
    def _output_selected_remaining():

# looks to be unused
def _output_panel_table(panels: list[frozenset[str]], probs: list[float]):
    def panel_to_tuple(panel: frozenset[str]) -> tuple[str]:

```

### Partially migrated

```python

```

### Fully migrated (or just deleted/replaced)

```python
class Settings:
    def __init__():
    def load_from_file(cls):
class SelectionError(Exception):
    def __init__(self, message):
class InfeasibleQuotasError(Exception):
    def __init__():
    def __str__(self):
class InfeasibleQuotasCantRelaxError(Exception):
    def __init__(self, message: str):

class PeopleAndCats:
    def __init__(self):
    def get_selected_file(self):
    def get_remaining_file(self):
    def _read_in_cats(self, cat_head, cat_body) -> tuple[list[str], int, int]:
    def _check_columns_exist_or_multiple(self, people_head, column_list, error_text):
    def _init_categories_people():

def create_readable_sample_file():

def get_people_at_same_address(people, pkey, check_same_address_columns):
def _same_address():
def _compute_households():
def really_delete_person(categories, people, pkey: str, *, selected: bool) -> None:
def delete_person():
def delete_all_in_cat(categories, people, cat_check_key, cat_check_value):
def find_max_ratio_cat(categories):

def _print(message: str) -> str:   # do we even want this?

# legacy selection stuff
def find_random_sample_legacy():

# modern selection alg stuff
def _relax_infeasible_quotas():
    def reduction_weight(feature, value):
def _setup_committee_generation():
def _find_any_committee():
def _ilp_results_to_committee(variables: dict[str, mip.entities.Var]) -> frozenset[str]:

# modern selection alg stuff
def pipage_rounding(marginals: list[tuple[Any, float]]) -> list[Any]:
def standardize_distribution():
def lottery_rounding():
def _distribution_stats():

# top level selection fn
def find_random_sample():

# modern selection alg stuff
def _generate_initial_committees():
def _dual_leximin_stage():
def find_distribution_leximin():
def _find_maximin_primal():
def find_distribution_maximin():
def _define_entitlements():
def _committees_to_matrix():
def find_distribution_nash():

# legacy selection stuff
def print_category_info(categories, people, people_selected, number_people_wanted):
def check_category_selected(categories, people, people_selected, number_selections):

# top level selection fn
def run_stratification():

```
