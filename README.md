# Git Plots

Package for plotting some basic information about a git repo as a function of time. There are many like it, but this one is mine.  
Shows line additions / deletions, number of commits and total lines of code.  
Currently only shows per day, but I will extend it so you can plot by week/month/year.

```python
import pandas as pd
from modules.df_functions import get_repo
from modules.plot_functions import plot

path = r"C:\Users\Tom\documents\coding\cityalarms\.git"
# or from a github repo
# path = "https://github.com/tommcdee/AI_search.git"
df = get_repo(path)
plot(df)
```

Can also trim off some commits at start and end of the history via the **start** and **end** parameters. Or, penalize commits that contain certain strings in their messages with the **penalties** parameter.  
For example, let's remove the first and last commits, retain only 25% of the lines for commits containing _"new typescript react project"_ and remove all the lines for commits containing _"corrected typos"_

```python
penalties = [("new typescript react project", 0.25), ("corrected typos", 0)]
df = get_repo(path, penalties, start=1, end=-1)
plot(df)
```
![History of my reboot of www.cityalarms.com](https://www.cityalarms.com/cityalarms.webp)
