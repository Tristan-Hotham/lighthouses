## Title

[OC] Every lighthouse in Wikidata, 9,770 of them, on one map: outside Sweden, building peaked in the 1870s, and the oldest still standing is Roman (AD 100)

## Body

I mapped every Wikidata item that is a lighthouse and has coordinates (9,770 after removing keepers' houses and replicas) and coloured them by the year they were built or first lit. Outside Sweden, new lights rise from 103 in the 1820s to 376 in the 1870s and fall to about 97 a decade after 1970 (automation, then satellite navigation). Per 1,000 km of coast (Natural Earth 1:10m), Sweden has 341 lights against 9.4 for the world. The big caveat: Wikidata coverage varies by country. Sweden's 2,555 lights (26% of the total) look like a national list loaded in full (96% have at most one Wikipedia article), while Indonesia has 12 and Nigeria none. Tallest heights come from Wikipedia's list because the Wikidata heights I had lost their units. Interactive map with a night glow view and search: https://maps.tristanhotham.com/lighthouses/

## Source comment

Sources: Wikidata (CC0), every item that is an instance of lighthouse (Q39715) or a subclass with coordinates, via QLever; Wikipedia contributors, List of tallest lighthouses (CC BY-SA 4.0); Natural Earth 1:10m countries and states (public domain), used to measure each coast as the country outline minus shared borders. Dates are Wikidata's earliest inception year, often the first light on the site rather than the present tower. "Still standing" was checked by hand for the oldest towers.

Tools: Python (pandas, shapely, pyproj, scipy, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/lighthouses/
Paper: https://doi.org/10.5281/zenodo.23857614
Blog post: https://blog.tristanhotham.com/2026/10/31/lighthouses/
