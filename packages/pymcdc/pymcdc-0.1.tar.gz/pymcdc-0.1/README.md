# pymcdc

A Python package to analyze and verify MC/DC (Modified Condition/Decision Coverage) criteria.

## Installation

```bash
pip install pymcdc
```

## 🚀 How to Use

```bash
python -m pymcdc foo.py
```
Analyzes the file `foo.py` and displays the condition combinations that must be satisfied for each decision.

```bash
python -m pymcdc --run foo.py
```
Executes `foo.py` and shows which MC/DC combinations were covered.

```bash
python -m pymcdc --run --append foo.py
```
Cumulatively runs `foo.py` and displays the MC/DC combinations covered across multiple runs.

```bash
python -m pymcdc --unittest test_foo.py foo.py
```
Runs `foo.py` using the test cases defined in `test_foo.py`.  
The `--unittest` argument can be used multiple times. The `--append` option is also supported here.

### 🔍 Example

```bash
python3 -m pymcdc bissexto.py
```

```
Line number: (5, 5)
Decision: a < 1 or a > 9999
Combinations to be covered: 
    | Result.   a < 1    a > 9999   Cover. 
-------------------------------------------
  1 |  False    False     False     False  
  2 |   True    True      False     False  
  3 |   True    False      True     False  

Run time: 0.00070 
```

```bash
python3 -m pymcdc --run bissexto.py
```

```
Line number: (5, 5)
Decision: a < 1 or a > 9999
Combinations to be covered: 
    | Result.   a < 1    a > 9999   Cover. 
-------------------------------------------
  1 |  False    False     False      True  
  2 |   True    True      False     False  
  3 |   True    False      True      True 
```

```bash
python3 -m pymcdc --unittest test_bissexto.py bissexto.py
```

```
Running tests...
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK

Line number: (5, 5)
Decision: a < 1 or a > 9999
Combinations to be covered: 
    | Result.   a < 1    a > 9999   Cover. 
-------------------------------------------
  1 |  False    False     False     False  
  2 |   True    True      False     False  
  3 |   True    False      True      True  
```

## 📝 Notes

1. The number of MC/DC requirements for a decision with `n` conditions is not always `n+1`. It can be slightly larger due to limitations in the computation algorithm.
2. For decisions with more than 15 conditions, the analysis may take a few minutes. This is only done once when using the `--append` option.

## 👤 Author

**Marcio Delamaro**

## 📄 License

MIT

## 🤝 Contributions

Feel free to open issues or submit pull requests!
