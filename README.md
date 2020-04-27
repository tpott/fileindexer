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

```
big_file_list --> many(file_list) --[map]--> fetch_files --> ngrams --[map]--> join(ngrams)
```

Problem is that for larger `ngrams * files` will cause join to crash.

# Challenge

Hypothetical size: 100TB in total across 200M distinct files. Numbers inspired by
[Sort Benchmark](https://sortbenchmark.org/). Useful for applications like
[VTGREP](https://blog.virustotal.com/2019/03/time-for-vt-enterprise-to-step-up.html).

For the sake of simplicity, assume that the minimum file size is 8 bytes (that's
small enough to fit in a single 64bit register!!) and max file size is 10GB.
This should make it interesting since some files will be much larger than the
average ~500KB.

This is also inspired by how simple [bashreduce](https://github.com/erikfrey/bashreduce)
seems to be. Ideally this project will be able to make something similar, but
be implemented in python. Assuming `map` functions are apart of the standard
toolchain, then the heavy CPU should be done outside of python anyways. `ssh`
and `scp` should be able to get a long ways for distributing work.

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

* [mlr](https://johnkerl.org/miller/doc/) for combining multiple CSVs/TSVs.
Example: `mlr --itsvlite --otsvlite cat ngrams1 ngrams2 ngrams3 ...`
* [jq](https://stedolan.github.io/jq/manual/) for manipulating JSON
