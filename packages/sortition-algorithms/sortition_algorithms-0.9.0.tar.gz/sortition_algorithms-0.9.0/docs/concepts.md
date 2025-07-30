# Core Concepts

Understanding these fundamental concepts is essential for effectively using sortition algorithms.

## What is Sortition?

**Sortition** is the random selection of representatives from a larger population, designed to create panels that reflect the demographic composition of the whole group. Unlike simple random sampling (which could accidentally select all men or all young people), sortition uses **stratified random selection** to ensure demographic balance.

### Historical Context

Sortition has ancient roots in Athenian democracy, where citizens were chosen by lot to serve in government. Modern applications include:

- **Citizens' Assemblies**: Groups that deliberate on policy issues
- **Deliberative Polls**: Representative samples for public opinion research
- **Jury Selection**: Court juries selected from voter rolls
- **Participatory Budgeting**: Community members deciding budget priorities

## Key Components

### Features and Feature Values

**Features** are demographic characteristics used for stratification:

- Gender, Age, Education, Income, Location, etc.

**Feature Values** are the specific categories within each feature:

- Gender: Male, Female, Non-binary
- Age: 18-30, 31-50, 51-65, 65+
- Location: Urban, Suburban, Rural

### Quotas and Targets

Each feature value has **minimum and maximum quotas** that define the acceptable range for selection:

```csv
feature,value,min,max
Gender,Male,45,55
Gender,Female,45,55
Age,18-30,20,30
Age,31-50,30,40
Age,51+,25,35
```

This ensures your panel of 100 people includes 45-55 men, 45-55 women, 20-30 young adults, etc.

### People Pool

The **candidate pool** contains all eligible individuals with their demographic data:

```csv
id,Name,Gender,Age,Location,Email
p001,Alice Smith,Female,18-30,Urban,alice@example.com
p002,Bob Jones,Male,31-50,Rural,bob@example.com
...
```

## Address Checking and Household Diversity

A critical feature for ensuring true representativeness is **address checking** - preventing multiple people from the same household being selected.

### Why Address Checking Matters

Without address checking, you might accidentally select:

- Multiple family members with similar views
- Several housemates from a shared address
- People who influence each other's opinions

This reduces the independence and diversity of your panel.

### How It Works

Configure address checking in your settings:

```python
settings = Settings(
    check_same_address=True,
    check_same_address_columns=["Address", "Postcode"]
)
```

When someone is selected:

1. The algorithm identifies anyone else with matching values in the specified columns
2. Those people are removed from the remaining pool
3. This ensures geographic and household diversity

### Address Column Strategies

**Single column approach**:

```python
check_same_address_columns = ["Full_Address"]
```

**Multi-column approach** (more flexible):

```python
check_same_address_columns = ["Street", "City", "Postcode"]
```

**Exact vs. fuzzy matching**: The current implementation requires exact string matches. For fuzzy address matching, you'd need to clean your data first.

## Selection Algorithms

Different algorithms optimize for different fairness criteria:

### Maximin (Default)

- **Goal**: Maximize the minimum selection probability
- **Good for**: Ensuring no group is severely underrepresented
- **Trade-off**: May not optimize overall fairness

### Nash

- **Goal**: Maximize the product of all selection probabilities
- **Good for**: Balanced representation across all groups
- **Trade-off**: Complex optimization, harder to interpret

### Leximin

- **Goal**: Lexicographic maximin (requires Gurobi license)
- **Good for**: Strict fairness guarantees
- **Trade-off**: Requires commercial solver

### Legacy

- **Goal**: Backwards compatibility with older implementations
- **Good for**: Reproducing historical selections
- **Trade-off**: Less sophisticated than modern algorithms

## The Selection Process

### 1. Feasibility Checking

Before selection begins, the algorithm verifies that quotas are achievable:

```python
features.check_desired(number_people_wanted=100)
```

### 2. Algorithm Execution

The chosen algorithm finds an optimal probability distribution over possible committees.

### 3. Lottery Rounding

The probability distribution is converted to concrete selections using randomized rounding.

### 4. Validation

Selected committees are checked against quotas to ensure targets were met.

## Randomness and Reproducibility

### Random Seeds

For reproducible results (e.g., for auditing), set a random seed:

```python
settings = Settings(random_number_seed=42)
```

### Security Considerations

For production use, avoid fixed seeds. The library uses Python's `secrets` module when no seed is specified.

## Data Quality Considerations

### Feature Consistency

Ensure feature values are consistent between your quotas file and candidate data:

```csv
# demographics.csv
Gender,Male,45,55
Gender,Female,45,55

# candidates.csv - values must match exactly
person1,Male,...    # ✅ Matches
person2,male,...    # ❌ Case mismatch
person3,M,...       # ❌ Abbreviation mismatch
```

### Missing Data

The library requires complete demographic data. Handle missing values before import:

- Impute missing values
- Create "Unknown" categories
- Exclude incomplete records

### Data Validation

The library performs extensive validation:

- Checks for unknown feature values
- Verifies quota feasibility
- Validates candidate pool size

## Error Handling

### Common Errors

**InfeasibleQuotasError**: Your quotas cannot be satisfied

```python
# Too restrictive - asking for 90+ males in a pool of 100
Gender,Male,90,100
Gender,Female,90,100
```

**SelectionError**: General selection failures

- Insufficient candidates in a category
- Conflicting constraints

**ValueError**: Invalid parameters

- Negative quotas
- Invalid algorithm names

### Debugging Tips

1. **Check quota feasibility**: Sum of minimums ≤ panel size ≤ sum of maximums
2. **Verify data consistency**: Feature values match between files
3. **Review messages**: The algorithm provides detailed feedback
4. **Test with relaxed quotas**: Temporarily widen ranges to isolate issues

## Best Practices

### Quota Design

- **Start conservative**: Use wider ranges initially, then narrow if needed
- **Consider interactions**: Age and education might be correlated
- **Plan for edge cases**: What if you have few candidates in a category?

### Data Preparation

- **Standardize values**: Consistent capitalization and spelling
- **Validate completeness**: No missing demographic data
- **Test with samples**: Verify your setup with small test runs

### Address Checking

- **Clean addresses first**: Standardize formatting before using address checking
- **Consider geography**: Urban areas might need tighter address matching
- **Balance household diversity vs. other constraints**: Address checking reduces your effective pool size

## Next Steps

Now that you understand the core concepts:

- **[Quick Start](quickstart.md)** - Try your first selection
- **[API Reference](api-reference.md)** - Detailed function documentation
- **[CLI Usage](cli.md)** - Command line examples
- **[Data Adapters](adapters.md)** - Working with different data sources
- **[Advanced Usage](advanced.md)** - Complex scenarios and optimization
