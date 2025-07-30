Functioning
===========

`sosia` (Italian for `doppelgänger <https://en.wikipedia.org/wiki/Doppelg%C3%A4nger>`_) is intended to create control groups for Diff-in-Diff analysis of scientists:  Some treatment happens to a scientist, and you need "similar" scientists to whom nothing happened.  Similiar means:

1. Publishes in sources (journals, book series, etc.) the scientist publishes too
2. Publishes in sources associated with the scientist's main field at least every X years
3. Publishes in the latest year the scientist did as well
4. Is not a co-author in the pre-phase
5. Optional: The main discpline is the same as that of the scientist
6. Optional: Started publishing around the same year as the scientist
7. Optional: In the year of comparison, has about the same number of publications
8. Optional: In the year of comparison, has about the same number of co-authors
9. Optional: In the year of comparison, has about the same number of citations (excluding self-ciations)

That steps 5 through 9 are optional means that there are no default values, and that you may want to choose to not use a particular filter.  Of course, it would not make sense to not use any of these filters.  Most authors will want to use steps 5 through 9, as this aligns most closely with the literature.

You obtain results after only four steps:

1. Initiate the class
2. Define search sources
3. Identify candidates
4. Filter the candidates to obtain a matching group

Depending on the number of search sources and of candidates, one search may easily take several hours. The :doc:`tutorial` takes nearly an hour. Users should start with small margins and a small chunk size and gradually increase the most binding margins.

Each query on the Scopus database will make use of your API Key, which allows several thousant requests per week per API. `sosia` and `pybliometrics` make sure that all information are cached, so that subsequent queries will take less than a minute.  As cached data will deprecate, the main classes and all methods have `refresh` parameters, which steer whether and when to refresh the cached queries (default is `False`, maybe be an integer as well).
