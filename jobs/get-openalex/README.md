# get-openalex (v0.1.0)

## CLI
To use `get-openalex` from the Command Line, install the python package (for example, `pip install .` after cloning). Then run:
```
get-openalex  --outDir "/Users/aithena/openalex/data" --fromDate "2020-01-01"
```
This would download everything beginning from 2020-01-01.

## Parameters
### Optional - onlyType
You can specify if you want to download only data for a specific OpenAlex Object:
```
get-openalex  --outDir "/Users/aithena/openalex/data" --fromDate "2020-01-01" --onlyType "Authors"
```
This, for example, would download only Authors.
The value of `onlyType` must be a single string:
one of the types of OpenAlex Objects (Authors, Works, Topics...)

### fromDate - FROM_DATE
`--fromDate` or the environment variable `FROM_DATE` will specify the **first** day from when data will be downloaded.
If no date is specified and the value of environment variable `ALL_MONTH` is either not set or it is set to `False` or `0`, **all the data** will be downloaded.
The date must follow ISO8601 format, for example: "2024-11-28"


### env: ALL_LAST_MONTH
If `ALL_LAST_MONTH` is set to `True` or `1`, when `get-openalex` is executed, the value of `fromDate` will be the result of executing:
```python
from datetime import date
today_ = date.today()
from_date = today_.replace(day=1, month=today_.month-1).isoformat()
```
so all data starting from the first day of the current month will be downloaded.
This would mean that the job needs to be ran on the first day of each month.
