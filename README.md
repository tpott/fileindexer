# fileindexer
Experimental pipeline

Simple data struct:

ngram:hex,num_distinct_files:count,file_list_len:count,file_list:json

* 1-grams can have 256 distinct values
* 2-grams can have ~65K distinct values
* 3-grams can have ~16M distinct values
* 4-grams can have ~4B distinct values
* 5-grams can have ~1T distinct values
* 6-grams can have ~250T distinct values

But if you only have 10M files that are ~100GB in total, then the number of
possible distinct values is capped, and likely much lower than the max.

Naive approach:

big_file_list --> many(file_list) --[map]--> fetch_files --> ngrams --[map]--> join(ngrams)

Problem is that for larger ngrams * files will cause join to crash.

# fileserver
In order to run `fetch_files` from above, we need some service to return file
content. This little utility starts a webserver.
```
python3 filelist.py ~ --md5 > filelist.tsv && python3 fileserver.py filelist.tsv
```

# filelist
In order for the webserver above to know what files to serve...
```
python3 filelist.py ~ | mlr --itsvlite --otsv sample -k 5
```

# Useful utilities:

* [mlr](https://johnkerl.org/miller/doc/) for combining multiple CSVs/TSVs
** `mlr --itsvlite --otsvlite cat ngrams1 ngrams2 ngrams3 ...`
* [jq](https://stedolan.github.io/jq/manual/) for manipulating JSON
